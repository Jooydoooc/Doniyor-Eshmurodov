"""
Database module — fully dynamic groups AND sections per level.

Tables:
- groups:   dynamic groups per level
- sections: dynamic sections per level
- content:  all teaching materials
- announcements: broadcast messages
- users:    student registry
"""

import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "student_bot.db"

LEVELS = ["Beginner", "Elementary", "Pre-IELTS", "IELTS Introduction", "IELTS Graduation"]

# Default groups seeded on first run
DEFAULT_GROUPS = ["Hunters", "Hackers", "Assassins"]

# Default sections seeded on first run for every level
DEFAULT_SECTIONS = ["Tasks", "Homework", "Materials", "Books", "Recorded Lessons", "Lesson Files"]

# Icons for known section names — admin can add new ones freely
SECTION_ICONS = {
    "Tasks": "📝",
    "Homework": "🏠",
    "Materials": "📚",
    "Books": "📖",
    "Recorded Lessons": "🎥",
    "Lesson Files": "📂",
    "Mock Tests": "📋",
    "Speaking Tasks": "🗣",
    "Writing Feedback": "✍️",
    "Vocabulary": "🔤",
    "Listening": "🎧",
    "Grammar": "📐",
    "Reading": "📰",
    "Announcements": "📣",
}


def get_section_icon(section_name: str) -> str:
    return SECTION_ICONS.get(section_name, "📌")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables and seed defaults."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            group_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(level, group_name)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            section_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(level, section_name)
        )
    """)

    cur.execute("""
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
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_seen TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed default groups if empty
    cur.execute("SELECT COUNT(*) as cnt FROM groups")
    if cur.fetchone()["cnt"] == 0:
        for level in LEVELS:
            for group in DEFAULT_GROUPS:
                cur.execute(
                    "INSERT OR IGNORE INTO groups (level, group_name, created_at) VALUES (?, ?, ?)",
                    (level, group, datetime.utcnow().isoformat()),
                )

    # Seed default sections if empty
    cur.execute("SELECT COUNT(*) as cnt FROM sections")
    if cur.fetchone()["cnt"] == 0:
        for level in LEVELS:
            for section in DEFAULT_SECTIONS:
                cur.execute(
                    "INSERT OR IGNORE INTO sections (level, section_name, created_at) VALUES (?, ?, ?)",
                    (level, section, datetime.utcnow().isoformat()),
                )

    conn.commit()
    conn.close()


# ─────────────────────────── GROUPS ───────────────────────────

def get_groups(level: str) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT group_name FROM groups WHERE level = ? ORDER BY group_name",
        (level,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r["group_name"] for r in rows]


def get_all_groups() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT level, group_name FROM groups ORDER BY level, group_name")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_group(level: str, group_name: str) -> bool:
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM groups WHERE level = ? AND group_name = ?", (level, group_name))
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute("DELETE FROM content WHERE level = ? AND group_name = ?", (level, group_name))
    conn.commit()
    conn.close()
    return deleted


def rename_group(level: str, old_name: str, new_name: str) -> bool:
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


# ─────────────────────────── SECTIONS ───────────────────────────

def get_sections(level: str) -> list:
    """Return all section names for a level, in creation order."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT section_name FROM sections WHERE level = ? ORDER BY id",
        (level,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r["section_name"] for r in rows]


def get_all_sections() -> list:
    """Return all (level, section_name) pairs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT level, section_name FROM sections ORDER BY level, id")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_section(level: str, section_name: str) -> bool:
    """Add a section to a level. Returns True if added, False if duplicate."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO sections (level, section_name, created_at) VALUES (?, ?, ?)",
            (level, section_name.strip(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_section(level: str, section_name: str) -> bool:
    """Delete a section and ALL its content for that level."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM sections WHERE level = ? AND section_name = ?",
        (level, section_name),
    )
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute(
            "DELETE FROM content WHERE level = ? AND section = ?",
            (level, section_name),
        )
    conn.commit()
    conn.close()
    return deleted


def rename_section(level: str, old_name: str, new_name: str) -> bool:
    """Rename a section and update all content rows."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE sections SET section_name = ? WHERE level = ? AND section_name = ?",
            (new_name.strip(), level, old_name),
        )
        if cur.rowcount == 0:
            return False
        cur.execute(
            "UPDATE content SET section = ? WHERE level = ? AND section = ?",
            (new_name.strip(), level, old_name),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ─────────────────────────── CONTENT ───────────────────────────

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


# ─────────────────────────── ANNOUNCEMENTS ───────────────────────────

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


# ─────────────────────────── USERS ───────────────────────────

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
