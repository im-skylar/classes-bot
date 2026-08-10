import sqlite3
import os
from contextlib import contextmanager
from typing import Any, Generator
import enum

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# This has to match the inserts in schema.sql!
class School(enum.IntEnum):
    Alteration = 1
    Conjuration = 2
    Illusion = 3
    Restoration = 4
    General_Studies = 5

    @property
    def display(self):
        return self.name.replace("_", " ")

class ClassesDB():
    def __init__(self, location: str = ":memory:") -> None:
        self.db_location = location
        self.conn = sqlite3.connect(self.db_location)

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

    """
    def get_schools(self) -> list[Any]:
        #List all schools.
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name, capacity FROM schools;")
        return cur.fetchall()

    def add_school(self, name: str, capacity: int) -> int|None:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO schools (name, capacity) VALUES (?, ?);", (name, capacity,))
        self.commit_or_rollback()
        return cur.lastrowid

    def update_school(self, id: int, name: str, capacity: int):
        self.conn.execute("UPDATE schools SET name = ?, capacity = ? WHERE id = ?;", (name, capacity, id,))
        self.commit_or_rollback()

    def delete_school(self, id: int):
        #Deletes school. Returns True if school existed, False if no change occured.
        cur = self.conn.cursor()
        cur.execute("UPDATE students SET first_choice = NULL WHERE first_choice = ?;", (id,))
        cur.execute("UPDATE students SET second_choice = NULL WHERE second_choice = ?;", (id,))
        cur.execute("DELETE FROM enrollments WHERE school = ?;", (id,))
        cur.execute("DELETE FROM schools WHERE id = ?;", (id,))
        self.commit_or_rollback()

    def get_school_name(self, id: int) -> str|None:
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM schools WHERE id = ?;", (id,))

        name = cur.fetchone()

        if not name:
            return None
        
        return name[0]
    
    def get_school_capacity_and_name(self, id: int) -> tuple[int,str]|None:
        cur = self.conn.cursor()
        cur.execute("SELECT capacity, name FROM schools WHERE id = ?;", (id,))

        name = cur.fetchone()

        if not name:
            return None
        
        return name

    def school_exists(self, id: int) -> bool:
        return self.get_school_capacity_and_name(id) is not None"""

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

        self.conn.execute("UPDATE students SET first_choice = ?, second_choice = ? WHERE discord_id = ?;", (first_choice, second_choice, discord_id,))
        self.commit_or_rollback()

    def get_choices(self, discord_id: int) -> tuple[School|None, School|None]:
        cur = self.conn.cursor()
        cur.execute("SELECT first_choice, second_choice FROM students WHERE discord_id = ?;", (discord_id,))
        return cur.fetchone()

    def assign_aptitudes(self, rerun: bool):
        self.conn.execute("UPDATE students SET roll = ABS(RANDOM() % 10000) WHERE first_choice IS NOT NULL AND NOT (ROLL = -1 AND ? = 1);", (rerun,))
        self.commit_or_rollback()

    def get_schools(self) -> list[tuple[int, int]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, capacity FROM schools;")
        return cur.fetchall()

    def find_applicants(self, prio: int, school: School, limit: int, second_choice = False) -> list[tuple[int]]:
        cur = self.conn.cursor()

        choice = "first_choice" if not second_choice else "second_choice"

        cur.execute(f"SELECT discord_id FROM students WHERE roll >= 10 AND priority = ? AND {choice} = ? ORDER BY roll DESC LIMIT ?;", (prio, school, limit))

        return cur.fetchall()

    def enroll_applicants(self, school: School, applicants: list[int]):
        self.conn.executemany("INSERT INTO enrollments (student, school) VALUES (?, ?);", [(app, school) for app in applicants])

        self.conn.executemany("UPDATE students SET priority = 0, roll = -1 WHERE discord_id = ?;", [(app,) for app in applicants])
        self.commit_or_rollback()

    def get_enrollments(self, school: School) -> list[int]:
        cur = self.conn.cursor()
        cur.execute("SELECT student FROM enrollments WHERE school = ?;", (school,))
        return [app[0] for app in cur.fetchall()]

