PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY,
    capacity INTEGER NOT NULL
);

-- This has to match the "School" enum in db.py
INSERT OR IGNORE INTO schools (id, capacity)
VALUES (1, 0), (2, 0), (3, 0), (4, 0), (5, 0);

CREATE TABLE IF NOT EXISTS students (
    discord_id      INTEGER PRIMARY KEY,

    first_choice    INTEGER,
    second_choice   INTEGER,
    
    -- Whether this person should be assigned before the others
    priority        INTEGER NOT NULL DEFAULT 0,
    roll            INTEGER DEFAULT NONE,

    school          INTEGER DEFAULT NONE,
    enroll_status   INTEGER DEFAULT NONE, -- references "Status" enum in db.py

    invt_msg_id     INTEGER DEFAULT NONE,
    invt_expires_on INTEGER DEFAULT NONE, -- UNIX time

    FOREIGN KEY (first_choice, second_choice)
    REFERENCES classes (id, id)
);

CREATE VIEW IF NOT EXISTS queue AS
SELECT
    discord_id,
    school,
    enroll_status,
    ROW_NUMBER() OVER (
        PARTITION BY school
        ORDER BY priority DESC, choice_rank ASC, roll ASC
    ) AS position
FROM (
    SELECT
        discord_id,
        priority,
        enroll_status,
        first_choice AS school,
        1 AS choice_rank,
        roll
    FROM students
    UNION ALL
    SELECT
        discord_id,
        priority,
        enroll_status,
        second_choice AS school,
        2 AS choice_rank,
        roll
    FROM students
) AS choices;
