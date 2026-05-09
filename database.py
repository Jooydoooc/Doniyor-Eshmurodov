"""
Database module.

Navigation structure:
  Main Menu → Category → [Day Type → Time Slot → Group] → Section → Content

Categories (main menu buttons):
  - Groups         → Odd Days / Even Days → Time → Group Name → Section
  - Universal      → Group Name → Section  (shared for all students)
  - Mock Tests     → Section
  - Telegram Channel → link/info

Tables:
  categories    — main menu items (Groups, Universal, Mock Tests, Telegram Channel, + custom)
  day_types     — Odd Days / Even Days (only used inside Groups category)
  time_slots    — 9:30-11:30, 14:30-16:30, etc. (belong to a day_type)
  group_names   — Hunters, Assassins, Hackers (shared across day_types/times)
  sections      — Tasks, Homework, etc. per category
  content       — all actual content rows
  announcements — broadcast messages
  users         — student registry
"""

import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "student_bot.db"

# ── Fixed defaults ──────────────────────────────────────────────

DEFAULT_CATEGORIES = ["Groups", "Universal", "Mock Tests", "Telegram Channel"]

DEFAULT_DAY_TYPES = ["Odd Days", "Even Days"]

DEFAULT_TIME_SLOTS = [
    "9:30-11:30",
    "14:30-16:30",
    "16:30-18:30",
    "18:30-20:30",
]

DEFAULT_GROUP_NAMES = ["Hunters", "Assassins", "Hackers"]

DEFAULT_SECTIONS = {
    "Groups":           ["Tasks", "Homework", "Materials", "Books", "Recorded Lessons", "Lesson Files"],
    "Universal":        ["Tasks", "Homework", "Materials", "Books", "Recorded Lessons", "Lesson Files"],
    "Mock Tests":       ["Mock Test Files", "Answer Keys", "Results", "Feedback"],
    "Telegram Channel": ["Channel Link", "Announcements", "Resources"],
}

SECTION_ICONS = {
    "Tasks": "📝", "Homework": "🏠", "Materials": "📚", "Books": "📖",
    "Recorded Lessons": "🎥", "Lesson Files": "📂", "Mock Test Files": "📋",
    "Answer Keys": "🔑", "Results": "📊", "Feedback": "✍️",
    "Channel Link": "🔗", "Announcements": "📣", "Resources": "📦",
    "Vocabulary": "🔤", "Listening": "🎧", "Grammar": "📐",
    "Speaking Tasks": "🗣", "Writing Feedback": "✍️", "Reading": "📰",
}


def get_section_icon(name: str) -> str:
    return SECTION_ICONS.get(name, "📌")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS day_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_type TEXT NOT NULL,
            slot TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(day_type, slot)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(category, name)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            day_type TEXT,
            time_slot TEXT,
            group_name TEXT,
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

    # Seed categories
    cur.execute("SELECT COUNT(*) as c FROM categories")
    if cur.fetchone()["c"] == 0:
        for i, cat in enumerate(DEFAULT_CATEGORIES):
            cur.execute(
                "INSERT OR IGNORE INTO categories (name, position, created_at) VALUES (?,?,?)",
                (cat, i, datetime.utcnow().isoformat()),
            )

    # Seed day types
    cur.execute("SELECT COUNT(*) as c FROM day_types")
    if cur.fetchone()["c"] == 0:
        for dt in DEFAULT_DAY_TYPES:
            cur.execute(
                "INSERT OR IGNORE INTO day_types (name, created_at) VALUES (?,?)",
                (dt, datetime.utcnow().isoformat()),
            )

    # Seed time slots
    cur.execute("SELECT COUNT(*) as c FROM time_slots")
    if cur.fetchone()["c"] == 0:
        for dt in DEFAULT_DAY_TYPES:
            for slot in DEFAULT_TIME_SLOTS:
                cur.execute(
                    "INSERT OR IGNORE INTO time_slots (day_type, slot, created_at) VALUES (?,?,?)",
                    (dt, slot, datetime.utcnow().isoformat()),
                )

    # Seed group names
    cur.execute("SELECT COUNT(*) as c FROM group_names")
    if cur.fetchone()["c"] == 0:
        for g in DEFAULT_GROUP_NAMES:
            cur.execute(
                "INSERT OR IGNORE INTO group_names (name, created_at) VALUES (?,?)",
                (g, datetime.utcnow().isoformat()),
            )

    # Seed sections per category
    cur.execute("SELECT COUNT(*) as c FROM sections")
    if cur.fetchone()["c"] == 0:
        for cat, secs in DEFAULT_SECTIONS.items():
            for sec in secs:
                cur.execute(
                    "INSERT OR IGNORE INTO sections (category, name, created_at) VALUES (?,?,?)",
                    (cat, sec, datetime.utcnow().isoformat()),
                )

    conn.commit()
    conn.close()


# ── CATEGORIES ───────────────────────────────────────────────────

def get_categories() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM categories ORDER BY position, id")
    rows = cur.fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_category(name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(position),0)+1 as next FROM categories")
    pos = cur.fetchone()["next"]
    try:
        cur.execute(
            "INSERT INTO categories (name, position, created_at) VALUES (?,?,?)",
            (name.strip(), pos, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_category(name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE name=?", (name,))
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute("DELETE FROM sections WHERE category=?", (name,))
        cur.execute("DELETE FROM content WHERE category=?", (name,))
    conn.commit()
    conn.close()
    return deleted


def rename_category(old: str, new: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE categories SET name=? WHERE name=?", (new.strip(), old))
        if cur.rowcount == 0:
            return False
        cur.execute("UPDATE sections SET category=? WHERE category=?", (new.strip(), old))
        cur.execute("UPDATE content SET category=? WHERE category=?", (new.strip(), old))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── DAY TYPES ────────────────────────────────────────────────────

def get_day_types() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM day_types ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_day_type(name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO day_types (name, created_at) VALUES (?,?)",
            (name.strip(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_day_type(name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM day_types WHERE name=?", (name,))
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute("DELETE FROM time_slots WHERE day_type=?", (name,))
        cur.execute("DELETE FROM content WHERE day_type=?", (name,))
    conn.commit()
    conn.close()
    return deleted


def rename_day_type(old: str, new: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE day_types SET name=? WHERE name=?", (new.strip(), old))
        if cur.rowcount == 0:
            return False
        cur.execute("UPDATE time_slots SET day_type=? WHERE day_type=?", (new.strip(), old))
        cur.execute("UPDATE content SET day_type=? WHERE day_type=?", (new.strip(), old))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── TIME SLOTS ───────────────────────────────────────────────────

def get_time_slots(day_type: str) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT slot FROM time_slots WHERE day_type=? ORDER BY id", (day_type,))
    rows = cur.fetchall()
    conn.close()
    return [r["slot"] for r in rows]


def get_all_time_slots() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT day_type, slot FROM time_slots ORDER BY day_type, id")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_time_slot(day_type: str, slot: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO time_slots (day_type, slot, created_at) VALUES (?,?,?)",
            (day_type, slot.strip(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_time_slot(day_type: str, slot: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM time_slots WHERE day_type=? AND slot=?", (day_type, slot))
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute("DELETE FROM content WHERE day_type=? AND time_slot=?", (day_type, slot))
    conn.commit()
    conn.close()
    return deleted


def rename_time_slot(day_type: str, old: str, new: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE time_slots SET slot=? WHERE day_type=? AND slot=?",
            (new.strip(), day_type, old),
        )
        if cur.rowcount == 0:
            return False
        cur.execute(
            "UPDATE content SET time_slot=? WHERE day_type=? AND time_slot=?",
            (new.strip(), day_type, old),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── GROUP NAMES ──────────────────────────────────────────────────

def get_group_names() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM group_names ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_group_name(name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO group_names (name, created_at) VALUES (?,?)",
            (name.strip(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_group_name(name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM group_names WHERE name=?", (name,))
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute("DELETE FROM content WHERE group_name=?", (name,))
    conn.commit()
    conn.close()
    return deleted


def rename_group_name(old: str, new: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE group_names SET name=? WHERE name=?", (new.strip(), old))
        if cur.rowcount == 0:
            return False
        cur.execute("UPDATE content SET group_name=? WHERE group_name=?", (new.strip(), old))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── SECTIONS ─────────────────────────────────────────────────────

def get_sections(category: str) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sections WHERE category=? ORDER BY id", (category,))
    rows = cur.fetchall()
    conn.close()
    return [r["name"] for r in rows]


def get_all_sections() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT category, name FROM sections ORDER BY category, id")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_section(category: str, name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO sections (category, name, created_at) VALUES (?,?,?)",
            (category, name.strip(), datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_section(category: str, name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sections WHERE category=? AND name=?", (category, name))
    deleted = cur.rowcount > 0
    if deleted:
        cur.execute("DELETE FROM content WHERE category=? AND section=?", (category, name))
    conn.commit()
    conn.close()
    return deleted


def rename_section(category: str, old: str, new: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE sections SET name=? WHERE category=? AND name=?",
            (new.strip(), category, old),
        )
        if cur.rowcount == 0:
            return False
        cur.execute(
            "UPDATE content SET section=? WHERE category=? AND section=?",
            (new.strip(), category, old),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── CONTENT ──────────────────────────────────────────────────────

def add_content(
    category: str,
    section: str,
    text: Optional[str] = None,
    file_id: Optional[str] = None,
    file_type: Optional[str] = None,
    caption: Optional[str] = None,
    day_type: Optional[str] = None,
    time_slot: Optional[str] = None,
    group_name: Optional[str] = None,
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO content
           (category, day_type, time_slot, group_name, section,
            text, file_id, file_type, caption, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (category, day_type, time_slot, group_name, section,
         text, file_id, file_type, caption, datetime.utcnow().isoformat()),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_content(
    category: str,
    section: str,
    day_type: Optional[str] = None,
    time_slot: Optional[str] = None,
    group_name: Optional[str] = None,
) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT * FROM content
           WHERE category=? AND section=?
             AND (day_type IS ? OR day_type=?)
             AND (time_slot IS ? OR time_slot=?)
             AND (group_name IS ? OR group_name=?)
           ORDER BY datetime(created_at) DESC""",
        (category, section,
         day_type, day_type,
         time_slot, time_slot,
         group_name, group_name),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_content_by_id(content_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM content WHERE id=?", (content_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_content_by_id(content_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM content WHERE id=?", (content_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ── ANNOUNCEMENTS ────────────────────────────────────────────────

def add_announcement(text: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO announcements (text, created_at) VALUES (?,?)",
        (text, datetime.utcnow().isoformat()),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_latest_announcement() -> Optional[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT text FROM announcements ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row["text"] if row else None


# ── USERS ────────────────────────────────────────────────────────

def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (user_id, username, first_name, last_seen) VALUES (?,?,?,?)
           ON CONFLICT(user_id) DO UPDATE SET
           username=excluded.username,
           first_name=excluded.first_name,
           last_seen=excluded.last_seen""",
        (user_id, username, first_name, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_user_ids() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [r["user_id"] for r in cur.fetchall()]
    conn.close()
    return ids
