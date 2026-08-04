import sqlite3
import os
from contextlib import contextmanager
from typing import Any, Generator

import discord

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

class ClassesDB():
    def __init__(self, location: str = ":memory:") -> None:
        self.db_location = location
        self.con = self._getcon()


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

    def get_classes(self, tutor: discord.User|None = None) -> list[Any]:
        """List all classes by a specific tutor. 
        
        Args:
            tutor: discord id of tutor to look for. leave empty to return all classes"""
        tutorid = 0
        list_all = tutor is None
        if not list_all:
            tutorid = tutor.id
        
        with self._getcon() as con:
            cur = con.cursor()
            cur.execute(
                """SELECT
                classes.id,
                classes.name,
                classes.dow,
                classes.time,
                classes.can_enroll,
                tutors.discord_id 
                FROM classes
                INNER JOIN tutors
                ON classes.tutor = tutors.id
                WHERE ? = 1
                OR (tutors.discord_id) = ?;""",
                (list_all, tutorid,))
            return cur.fetchall()

    def add_tutor_or_ignore(self, id: int) -> int:
        with self._getcon() as con:
            con.execute("INSERT OR IGNORE INTO tutors (discord_id) VALUES (?);", (id,))
            con.commit()

            cur = con.cursor()
            cur.execute("SELECT id FROM tutors WHERE discord_id = ?;", (id,))
            return cur.fetchone()[0]
            


    def add_class(self, name: str, dow: int, time: str, tutor_id: int):
        with self._getcon() as con:
            tutor = self.add_tutor_or_ignore(tutor_id)

            con.execute(
                """INSERT INTO classes
                (name, dow, time, tutor)
                VALUES (?, ?, ?, ?);
""", (name, dow, time, tutor)
            )