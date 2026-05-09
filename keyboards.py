"""
Keyboard module.
Builds inline keyboards (buttons) used throughout the bot.

Callback data format:
- "level:<level>"             when picking a level
- "group:<level>:<group>"     when picking a group
- "section:<level>:<group>:<section>"  when picking a section
- "back:levels"               return to levels menu
- "back:groups:<level>"       return to groups menu for a level
- "back:sections:<level>:<group>"  return to sections menu

We use '|' as the separator instead of ':' inside values when needed,
but since our level/group/section names don't contain ':' it's safe.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import LEVELS, GROUPS, SECTIONS


def levels_keyboard() -> InlineKeyboardMarkup:
    """Top-level menu: choose a level."""
    builder = InlineKeyboardBuilder()
    for level in LEVELS:
        builder.button(text=level, callback_data=f"level|{level}")
    builder.adjust(1)  # one button per row for readability
    return builder.as_markup()


def groups_keyboard(level: str) -> InlineKeyboardMarkup:
    """Second menu: choose a group inside a level."""
    builder = InlineKeyboardBuilder()
    for group in GROUPS:
        builder.button(text=group, callback_data=f"group|{level}|{group}")
    builder.button(text="⬅️ Back to Levels", callback_data="back|levels")
    builder.adjust(1)
    return builder.as_markup()


def sections_keyboard(level: str, group: str) -> InlineKeyboardMarkup:
    """Third menu: choose a section inside a group."""
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
    """Single 'back' button shown after content is delivered."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ Back to Sections",
        callback_data=f"back|sections|{level}|{group}",
    )
    builder.adjust(1)
    return builder.as_markup()


# ---------- ADMIN KEYBOARDS ----------

def admin_levels_keyboard(action: str) -> InlineKeyboardMarkup:
    """Admin picks a level when adding content. action is 'add' or 'delete'."""
    builder = InlineKeyboardBuilder()
    for level in LEVELS:
        builder.button(text=level, callback_data=f"adm|{action}|lvl|{level}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def admin_groups_keyboard(action: str, level: str) -> InlineKeyboardMarkup:
    """Admin picks a group when adding content."""
    builder = InlineKeyboardBuilder()
    for group in GROUPS:
        builder.button(
            text=group,
            callback_data=f"adm|{action}|grp|{level}|{group}",
        )
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def admin_sections_keyboard(action: str, level: str, group: str) -> InlineKeyboardMarkup:
    """Admin picks a section when deleting content (for show/delete flows)."""
    builder = InlineKeyboardBuilder()
    for section in SECTIONS:
        builder.button(
            text=section,
            callback_data=f"adm|{action}|sec|{level}|{group}|{section}",
        )
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()
