-- meetings: one row per uploaded audio file
CREATE TABLE IF NOT EXISTS meetings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    filename    TEXT NOT NULL,
    duration    REAL,
    status      TEXT DEFAULT 'pending',
    created_at  TEXT DEFAULT (datetime('now'))
);

-- results: the AI output for each meeting
CREATE TABLE IF NOT EXISTS results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL REFERENCES meetings(id),
    transcript      TEXT,
    summary         TEXT,
    action_items    TEXT,
    key_decisions   TEXT,
    model_used      TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- segments: per-sentence timestamps for transcript view
CREATE TABLE IF NOT EXISTS segments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id  INTEGER NOT NULL REFERENCES meetings(id),
    start_time  REAL,
    end_time    REAL,
    text        TEXT
);