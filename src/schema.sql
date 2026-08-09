PRAGMA foreign_keys = ON;

/*
CREATE TABLE IF NOT EXISTS tutors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id INTEGER UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dow INTEGER NOT NULL,
    time TEXT NOT NULL,
    tutor INTEGER NOT NULL,
    can_enroll INTEGER DEFAULT FALSE,
    FOREIGN KEY(tutor) REFERENCES tutors(id)
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id INTEGER NOT NULL
);

-- enrollments
CREATE TABLE IF NOT EXISTS student_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class INTEGER NOT NULL,
    student INTEGER NOT NULL,
    FOREIGN KEY(class) REFERENCES classes (id),
    FOREIGN KEY(student) REFERENCES students (id)
);
*/
--- New Schema:

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
