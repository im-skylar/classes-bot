import sqlite3
import os
from contextlib import contextmanager
from typing import Any, Generator
import enum
import datetime
import csv
import io

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

sqlite3.register_adapter(datetime.datetime, lambda x: int(x.timestamp()))

# This has to match the inserts in schema.sql!
class School(enum.IntEnum):
    Alteration      = 1
    Conjuration     = 2
    Illusion        = 3
    Restoration     = 4
    General_Studies = 5

    @property
    def display(self):
        return self.name.replace("_", " ")

class Status(enum.IntEnum):
    Unsent   = 0
    Pending  = 1 # waiting for reply
    Accepted = 2
    Denied   = 3
    Expired  = 4
    Waiting  = 5 # student is waiting for queue
    @property
    def display(self):
        return self.name

MAX_PRIO = 3

class ClassesDB():
    def __init__(self, location: str = ":memory:") -> None:
        self.db_location = location
        self.conn = sqlite3.connect(self.db_location)
        self.max_prio = MAX_PRIO
        self.pass_amount = 10
        self.max_roll = 20 # for testing, set to 20 later

    def close(self):
        self.conn.close()

    def commit_or_rollback(self):
        try:
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    @contextmanager
    def _getcon(self) -> Generator[sqlite3.Connection, Any, None]:
        """Commits on success and rolls back on error"""
        conn = sqlite3.connect(self.db_location)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        with open(SCHEMA_PATH) as scheme:
            with self._getcon() as con:
                con.executescript(scheme.read())

    def student_exists(self, discord_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT discord_id FROM students WHERE discord_id = ?;", (discord_id,))

        id = cur.fetchone()

        return id is not None

    def add_student(self, discord_id: int):
        self.conn.execute("INSERT INTO students (discord_id) VALUES (?);", (discord_id,))
        self.commit_or_rollback()

    def update_choices(self, discord_id: int, first_choice: School|None, second_choice: School|None):
        if not self.student_exists(discord_id):
            self.add_student(discord_id)

        self.conn.execute(
            """UPDATE students SET
            first_choice = ?,
            second_choice = ?
            WHERE discord_id = ?;""",
            (first_choice, second_choice, discord_id,))
        self.commit_or_rollback()

    def get_choices(self, discord_id: int) -> tuple[School|None, School|None]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT first_choice, second_choice FROM students WHERE discord_id = ?;",
            (discord_id,))
        return cur.fetchone()

    def get_capacities(self) -> list[tuple[int, int]]:
        """Returns how many seats are left for each school"""
        cur = self.conn.cursor()
        cur.execute("""SELECT
        id,
        capacity - (
            SELECT COUNT(*) FROM students
            WHERE school = id AND (enroll_status = ? OR enroll_status = ?)
        ) AS capacity_left
        FROM schools;""", (Status.Pending, Status.Accepted))
        return cur.fetchall()

    def get_enrollments(self, school: School) -> list[int]:
        cur = self.conn.cursor()

        cur.execute("""
        SELECT discord_id FROM students
        WHERE enroll_status = ? AND school = ?;
        """, (Status.Accepted, school,))
        
        return [app[0] for app in cur.fetchall()]

    def change_capacity(self, school: School, new_capacity: int):
        self.conn.execute("UPDATE schools SET capacity = ? WHERE id = ?;",
            (new_capacity, school,))
        self.commit_or_rollback()

    def set_enrollment_status(
            self,
            user_id: int,
            status: Status,
            message: int|None = None,
            expiry: datetime.datetime|None = None,
            school: School|None = None
        ):
        """This updates all the fields of the specified user,
        **notably NULLing every missing argument!**"""
        self.conn.execute("""
            UPDATE students
            SET 
                enroll_status = ?,
                invt_msg_id = ?,
                invt_expires_on = ?,
                school = ?
            WHERE discord_id = ?;""",
            (status, message, expiry, school, user_id,))
        self.commit_or_rollback()

    def accept_enrollment(self, user_id: int):
        self.conn.execute("""
            UPDATE students SET
                enroll_status = ?,
                priority = 0,
                invt_msg_id = NULL,
                invt_expires_on = NULL
            WHERE discord_id = ?;""", (Status.Accepted, user_id,))
        self.commit_or_rollback()

    def reset_enrolls(self):
        self.conn.execute("""
            UPDATE students
            SET
                roll = RANDOM() % ?,
                school = NULL,
                enroll_status = ?,
                invt_msg_id = NULL,
                invt_expires_on = NULL;
                
            UPDATE students
            SET
                priority = MIN(?+1, priority+1)
            WHERE
                first_choice <> NULL AND
                second_choice <> NULL;
        """, (self.max_roll, Status.Unsent, self.max_prio))

        self.commit_or_rollback()
    
    def get_queue(self, school: School, count: int, status: Status):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT DISTINCT discord_id
        FROM queue
        WHERE enroll_status = ? AND school = ?
        ORDER BY position ASC
        LIMIT ?;""", (status, school, count,))

        return [x[0] for x in cur.fetchall()]

    def get_users_school(self, id: int) -> School|None:
        cur = self.conn.cursor()

        cur.execute("SELECT school FROM students WHERE discord_id = ?;", (id,))

        # I think these Index None but it might be okay, bc there's no situation
        # when we might fetch a user not present in the db yet.
        return cur.fetchone()[0] 

    def get_users_message(self, id: int) -> int|None:
        cur = self.conn.cursor()
        cur.execute("SELECT invt_msg_id FROM students WHERE discord_id = ?;", (id,))

        return cur.fetchone()[0]

    def get_expired_invites(self, as_of: datetime.datetime) -> list[tuple[int, int]]:
        """Returns `discord_id` and `invt_msg_id`"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT discord_id, invt_msg_id FROM students WHERE invt_expires_on < ?;
        """, (as_of,))
        return cur.fetchall()

    def csv_export(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT discord_id, first_choice, second_choice, priority, roll, school, enroll_status FROM students;
        """)

        def ds(x: int | None) -> str:
            """Display school or none"""
            if x is None:
                return ""
            return School(x).display

        def dst(x: int | None) -> str:
            """Display Status or none"""
            if x is None:
                return ""
            return Status(x).display
        
        flike = io.StringIO()
        writer = csv.writer(flike)
        writer.writerow(("discord_id", "first_choice", "second_choice", "priority", "roll", "school", "status"))

        while row := cur.fetchone():
            (id, fc, sc, prio, roll, sch, stat) = row
            writer.writerow((
                id,
                ds(fc),
                ds(sc),
                prio,
                roll,
                ds(sch),
                dst(stat)))

        return flike


    def set_priority(self, discord_id: int, prio: int):
        if not self.student_exists(discord_id):
            self.add_student(discord_id)

        rows = self.conn.execute("UPDATE students SET priority = ? WHERE discord_id = ?", (discord_id, prio)).rowcount

        self.commit_or_rollback()

        return rows