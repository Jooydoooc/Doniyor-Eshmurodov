"""
Database module.
Handles all SQLite operations for the bot.

Tables:
- groups:  dynamic groups per level (replaces hardcoded GROUPS list)
- content: all teaching materials
- announcements: broadcast messages
- users: student registry for broadcasting
"""

import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "student_bot.db"

# Levels stay fixed (change here if needed)
LEVELS = ["Beginner", "Elementary", "Pre-IELTS", "IELTS Introduction", "IELTS Graduation"]

# Sections stay fixed
SECTIONS = ["Tasks", "Homework", "Materials", "Books", "Recorded Lessons", "Lesson Files"]

# Default groups loaded into DB on first run
DEFAULT_GROUPS = ["Hunters", "Hackers", "Assassins"]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables and seed default groups."""
    conn = get_connection()
    cur = conn.cursor()

    # Groups table — dynamic, editable by admin
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            group_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(level, group_name)
        )
        """
    )

    # Content table
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

    # Announcements table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Users table
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

    # Seed default groups for every level if table is empty
    cur.execute("SELECT COUNT(*) as cnt FROM groups")
    row = cur.fetchone()
    if row["cnt"] == 0:
        for level in LEVELS:
            for group in DEFAULT_GROUPS:
                cur.execute(
                    "INSERT OR IGNORE INTO groups (level, group_name, created_at) VALUES (?, ?, ?)",
                    (level, group, datetime.utcnow().isoformat()),
                )
        conn.commit()

    conn.close()


# ---------- GROUPS ----------

def get_groups(level: str) -> list:
    """Return all group names for a level, alphabetically."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT group_name FROM groups WHERE level = ? ORDER BY group_name",
        (level,),
    )
    rows = cur.fetchall()
    conn.close()
    return [row["group_name"] for row in rows]


def get_all_groups() -> list:
    """Return all (level, group_name) pairs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT level, group_name FROM groups ORDER BY level, group_name")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_group(level: str, group_name: str) -> bool:
    """Add a new group to a level. Returns True if added, False if already exists."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO groups (level, group_name, created_at) VALUES (?, ?, ?)",
            (level, group_name.strip(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_group(level: str, group_name: str) -> bool:
    """Delete a group and ALL its content. Returns True if deleted."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM groups WHERE level = ? AND group_name = ?",
        (level, group_name),
    )
    deleted = cur.rowcount > 0
    if deleted:
        # Also remove all content belonging to this group
        cur.execute(
            "DELETE FROM content WHERE level = ? AND group_name = ?",
            (level, group_name),
        )
    conn.commit()
    conn.close()
    return deleted


def rename_group(level: str, old_name: str, new_name: str) -> bool:
    """Rename a group and update all its content rows. Returns True if successful."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE groups SET group_name = ? WHERE level = ? AND group_name = ?",
            (new_name.strip(), level, old_name),
        )
        if cur.rowcount == 0:
            return False
        cur.execute(
            "UPDATE content SET group_name = ? WHERE level = ? AND group_name = ?",
            (new_name.strip(), level, old_name),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
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


def get_content(level: str, group_name: str, section: str) -> list:
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


def get_content_by_id(content_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content WHERE id = ?", (content_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_content(content_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM content WHERE id = ?", (content_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ---------- ANNOUNCEMENTS ----------

def add_announcement(text: str) -> int:
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


def get_all_user_ids() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [row["user_id"] for row in cur.fetchall()]
    conn.close()
    return ids
