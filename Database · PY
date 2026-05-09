"""
Database module.
Handles all SQLite operations for the bot.

Tables:
- content: stores all teaching materials (homework, tasks, books, etc.)

Each content row has:
  id, level, group_name, section, content_type, text, file_id, file_type, created_at
"""

import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "student_bot.db"

# These are the fixed levels and groups in your learning center
LEVELS = ["Beginner", "Elementary", "Pre-IELTS", "IELTS Introduction", "IELTS Graduation"]
GROUPS = ["Hunters", "Hackers", "Assassins"]
SECTIONS = ["Tasks", "Homework", "Materials", "Books", "Recorded Lessons", "Lesson Files"]


def get_connection() -> sqlite3.Connection:
    """Open a new connection to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            group_name TEXT NOT NULL,
            section TEXT NOT NULL,
            text TEXT,
            file_id TEXT,
            file_type TEXT,
            caption TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # Announcements table (broadcast to everyone, no level/group)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    # Track student users so admin can broadcast announcements
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_seen TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------- CONTENT ----------

def add_content(
    level: str,
    group_name: str,
    section: str,
    text: Optional[str] = None,
    file_id: Optional[str] = None,
    file_type: Optional[str] = None,
    caption: Optional[str] = None,
) -> int:
    """Insert a new content item. Returns its row id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO content (level, group_name, section, text, file_id, file_type, caption, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (level, group_name, section, text, file_id, file_type, caption, datetime.utcnow().isoformat()),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_content(level: str, group_name: str, section: str) -> list[sqlite3.Row]:
    """Fetch all content for a given level/group/section, newest first."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM content
        WHERE level = ? AND group_name = ? AND section = ?
        ORDER BY datetime(created_at) DESC
        """,
        (level, group_name, section),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_content_by_id(content_id: int) -> Optional[sqlite3.Row]:
    """Fetch one content item by its id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content WHERE id = ?", (content_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_content(content_id: int) -> bool:
    """Delete a content item by id. Returns True if a row was deleted."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM content WHERE id = ?", (content_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ---------- ANNOUNCEMENTS ----------

def add_announcement(text: str) -> int:
    """Save an announcement to the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO announcements (text, created_at) VALUES (?, ?)",
        (text, datetime.utcnow().isoformat()),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


# ---------- USERS ----------

def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    """Insert or update a user record (used for broadcasting announcements)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (user_id, username, first_name, last_seen)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_seen = excluded.last_seen
        """,
        (user_id, username, first_name, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_user_ids() -> list[int]:
    """Return every user_id we've ever seen."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [row["user_id"] for row in cur.fetchall()]
    conn.close()
    return ids
