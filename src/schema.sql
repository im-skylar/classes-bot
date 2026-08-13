PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY,
    capacity INTEGER NOT NULL
);

-- This has to match the "School" enum in db.py
INSERT OR IGNORE INTO schools (id, capacity) VALUES (1, 0), (2, 0), (3, 0), (4, 0), (5, 0);

CREATE TABLE IF NOT EXISTS students (
    discord_id INTEGER PRIMARY KEY,
    first_choice INTEGER,
    second_choice INTEGER,
    roll INTEGER,
    priority INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(first_choice, second_choice) REFERENCES classes (id, id)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student INTEGER NOT NULL,
    school INTEGER NOT NULL,
    FOREIGN KEY (student) REFERENCES students (discord_id),
    FOREIGN KEY (school) REFERENCES schools (id)
);
