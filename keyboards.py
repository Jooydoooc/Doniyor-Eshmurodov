"""
Keyboard module.
All keyboards now use dynamic groups fetched from the database.
"""

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import LEVELS, SECTIONS, get_groups


def levels_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in LEVELS:
        builder.button(text=level, callback_data=f"level|{level}")
    builder.adjust(1)
    return builder.as_markup()


def groups_keyboard(level: str) -> InlineKeyboardMarkup:
    """Groups are loaded dynamically from the database."""
    builder = InlineKeyboardBuilder()
    groups = get_groups(level)
    if groups:
        for group in groups:
            builder.button(text=group, callback_data=f"group|{level}|{group}")
    else:
        builder.button(text="⚠️ No groups yet", callback_data="noop")
    builder.button(text="⬅️ Back to Levels", callback_data="back|levels")
    builder.adjust(1)
    return builder.as_markup()


def sections_keyboard(level: str, group: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    icons = {
        "Tasks": "📝",
        "Homework": "🏠",
        "Materials": "📚",
        "Books": "📖",
        "Recorded Lessons": "🎥",
        "Lesson Files": "📂",
    }
    for section in SECTIONS:
        icon = icons.get(section, "•")
        builder.button(
            text=f"{icon} {section}",
            callback_data=f"section|{level}|{group}|{section}",
        )
    builder.button(text="⬅️ Back to Groups", callback_data=f"back|groups|{level}")
    builder.adjust(1)
    return builder.as_markup()


def back_to_sections_keyboard(level: str, group: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ Back to Sections",
        callback_data=f"back|sections|{level}|{group}",
    )
    builder.adjust(1)
    return builder.as_markup()


# ---------- ADMIN KEYBOARDS ----------

def admin_levels_keyboard(action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in LEVELS:
        builder.button(text=level, callback_data=f"adm|{action}|lvl|{level}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def admin_groups_keyboard(action: str, level: str) -> InlineKeyboardMarkup:
    """Show existing groups for admin actions (delete, rename, add content)."""
    builder = InlineKeyboardBuilder()
    groups = get_groups(level)
    if groups:
        for group in groups:
            builder.button(
                text=group,
                callback_data=f"adm|{action}|grp|{level}|{group}",
            )
    else:
        builder.button(text="⚠️ No groups for this level", callback_data="noop")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def admin_sections_keyboard(action: str, level: str, group: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for section in SECTIONS:
        builder.button(
            text=section,
            callback_data=f"adm|{action}|sec|{level}|{group}|{section}",
        )
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


# ---------- REPLY KEYBOARD ----------

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 My Level"),
                KeyboardButton(text="ℹ️ Help"),
            ],
            [
                KeyboardButton(text="📣 Announcements"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Choose an option...",
    )
