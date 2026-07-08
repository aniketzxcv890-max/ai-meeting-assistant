import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join("data", "meetings.db")
SCHEMA_PATH = os.path.join("app", "database", "schema.sql")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """Open and return a database connection."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name like a dict
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK relationships
    return conn


def init_db():
    """Create all tables from schema.sql if they don't exist yet."""
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r") as f:
            sql = f.read()
        conn.executescript(sql)


# ---------------------------------------------------------------------------
# MEETINGS table — one row per uploaded audio file
# ---------------------------------------------------------------------------
def create_meeting(title: str, filename: str) -> int:
    """
    Insert a new meeting row and return its auto-generated ID.
    Status starts as 'pending' — updated as processing progresses.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO meetings (title, filename, status)
            VALUES (?, ?, 'pending')
            """,
            (title, filename),
        )
        return cursor.lastrowid  # the new meeting's ID


def update_meeting_status(meeting_id: int, status: str, duration: float = None):
    """
    Update the processing status of a meeting.
    Valid statuses: pending | processing | done | error
    """
    with get_connection() as conn:
        if duration is not None:
            conn.execute(
                "UPDATE meetings SET status=?, duration=? WHERE id=?",
                (status, duration, meeting_id),
            )
        else:
            conn.execute(
                "UPDATE meetings SET status=? WHERE id=?",
                (status, meeting_id),
            )


def get_all_meetings() -> list[dict]:
    """
    Return all meetings ordered by most recent first.
    Used for the history page.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM meetings ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_meeting_by_id(meeting_id: int) -> dict | None:
    """Return a single meeting row as a dict, or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM meetings WHERE id=?", (meeting_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_meeting(meeting_id: int):
    """
    Delete a meeting and all its related data.
    The CASCADE behaviour is handled by deleting results and segments first,
    then the meeting itself.
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM segments WHERE meeting_id=?", (meeting_id,))
        conn.execute("DELETE FROM results  WHERE meeting_id=?", (meeting_id,))
        conn.execute("DELETE FROM meetings WHERE id=?",         (meeting_id,))


# ---------------------------------------------------------------------------
# RESULTS table — LLM analysis output
# ---------------------------------------------------------------------------
def save_results(
    meeting_id: int,
    transcript: str,
    summary: str,
    action_items: list[dict],
    key_decisions: list[str],
    model_used: str,
) -> int:
    """
    Save the full AI analysis for a meeting.
    action_items and key_decisions are stored as JSON strings.
    Returns the new result row ID.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO results
                (meeting_id, transcript, summary, action_items, key_decisions, model_used)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                meeting_id,
                transcript,
                summary,
                json.dumps(action_items),    # list → JSON string
                json.dumps(key_decisions),   # list → JSON string
                model_used,
            ),
        )
        return cursor.lastrowid


def get_results(meeting_id: int) -> dict | None:
    """
    Retrieve analysis results for a meeting.
    Automatically parses action_items and key_decisions back from JSON.
    Returns None if results don't exist yet.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM results WHERE meeting_id=?", (meeting_id,)
        ).fetchone()

        if not row:
            return None

        result = dict(row)
        # Parse JSON strings back into Python lists
        result["action_items"]  = json.loads(result["action_items"]  or "[]")
        result["key_decisions"] = json.loads(result["key_decisions"] or "[]")
        return result


# ---------------------------------------------------------------------------
# SEGMENTS table — per-sentence transcript with timestamps
# ---------------------------------------------------------------------------
def save_segments(meeting_id: int, segments: list[dict]):
    """
    Save all transcript segments for a meeting.
    Each segment has: start_time, end_time, text
    """
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO segments (meeting_id, start_time, end_time, text)
            VALUES (?, ?, ?, ?)
            """,
            [
                (meeting_id, seg["start_time"], seg["end_time"], seg["text"])
                for seg in segments
            ],
        )


def get_segments(meeting_id: int) -> list[dict]:
    """Return all transcript segments for a meeting, in time order."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM segments WHERE meeting_id=? ORDER BY start_time",
            (meeting_id,),
        ).fetchall()
        return [dict(row) for row in rows]