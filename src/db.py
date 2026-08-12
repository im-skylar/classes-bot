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
        self.max_roll = 100000 # for testing, set to 20 later

        """Minimum amount roll needed to be considered for assigning, needs to be >= 0."""
        self.pass_roll = 1

        assert self.pass_roll >= 0
        assert self.max_roll > self.pass_roll


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

        self.conn.execute("UPDATE students SET first_choice = ?, second_choice = ? WHERE discord_id = ?;", (first_choice, second_choice, discord_id,))
        self.commit_or_rollback()

    def get_choices(self, discord_id: int) -> tuple[School|None, School|None]:
        cur = self.conn.cursor()
        cur.execute("SELECT first_choice, second_choice FROM students WHERE discord_id = ?;", (discord_id,))
        return cur.fetchone()

    def assign_aptitudes(self, rerun: bool):
        """Assign aptitude values for studednts with choices set and, if it is a rerun, don't have their roll set to -1, meaning they already got assigned."""

        self.conn.execute("UPDATE students SET roll = ABS(RANDOM() % ?) WHERE first_choice IS NOT NULL AND NOT (ROLL = -1 AND ? = 1);", (self.max_roll, rerun,))
        self.commit_or_rollback()

    def get_schools(self) -> list[tuple[int, int]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, capacity FROM schools;")
        return cur.fetchall()

    def find_applicants(self, prio: int, school: School, limit: int, second_choice = False) -> list[tuple[int]]:
        """Finds [limit] applicants for the specified priority [prio] and school [school] by their {first_choice}, unless [second_choice] is set, then their {second_choice}.
        
        Because {roll} needs to be above self.pass_roll, applicants with {roll} == -1 (that already got assigned) won't be assigned a second time."""
        cur = self.conn.cursor()

        choice = "first_choice" if not second_choice else "second_choice"

        cur.execute(f"SELECT discord_id FROM students WHERE roll >= ? AND priority = ? AND {choice} = ? ORDER BY roll DESC LIMIT ?;", (self.pass_roll, prio, school, limit))

        return cur.fetchall()

    def enroll_applicants(self, school: School, applicants: list[int]):
        """Enrolls a list of applicants all to one school, setting their {roll} to -1, marking them as assigned so they won't be assigned again."""

        self.conn.executemany("INSERT INTO enrollments (student, school) VALUES (?, ?);", [(app, school) for app in applicants])

        self.conn.executemany("UPDATE students SET priority = 0, roll = -1 WHERE discord_id = ?;", [(app,) for app in applicants])
        self.commit_or_rollback()

    def get_enrollments(self, school: School) -> list[int]:
        cur = self.conn.cursor()
        cur.execute("SELECT student FROM enrollments WHERE school = ?;", (school,))
        return [app[0] for app in cur.fetchall()]

