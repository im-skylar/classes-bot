import sqlite3
import os
from contextlib import contextmanager
from typing import Any, Generator

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

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

    def get_schools(self) -> list[Any]:
        """List all schools."""
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
        """Deletes school. Returns True if school existed, False if no change occured."""
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
        return self.get_school_capacity_and_name(id) is not None
    