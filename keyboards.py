"""
Keyboards — all buttons are built dynamically from the database.

Student navigation:
  Main Menu → Category
    Groups       → Day Type → Time Slot → Group Name → Section → Content
    Universal    → Group Name → Section → Content
    Mock Tests   → Section → Content
    Telegram Ch. → Section → Content
    (custom)     → Section → Content
"""

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import (
    get_categories, get_day_types, get_time_slots,
    get_group_names, get_sections, get_section_icon,
)

# ── REPLY KEYBOARD (permanent bottom bar) ────────────────────────

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⚡ Groups"),
                KeyboardButton(text="🔮 Universal"),
            ],
            [
                KeyboardButton(text="🎯 Mock Tests"),
                KeyboardButton(text="🚀 Channel"),
            ],
            [
                KeyboardButton(text="💬 Announcements"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Choose a category...",
    )


# ── STUDENT INLINE KEYBOARDS ─────────────────────────────────────

def categories_keyboard() -> InlineKeyboardMarkup:
    """Main menu — all categories from DB."""
    builder = InlineKeyboardBuilder()
    cats = get_categories()
    icons = {
        "Groups": "👥",
        "Universal": "🌐",
        "Mock Tests": "📋",
        "Telegram Channel": "📢",
    }
    for cat in cats:
        icon = icons.get(cat, "📌")
        builder.button(text=f"{icon} {cat}", callback_data=f"cat|{cat}")
    builder.adjust(1)
    return builder.as_markup()


def day_types_keyboard(category: str) -> InlineKeyboardMarkup:
    """Odd Days / Even Days."""
    builder = InlineKeyboardBuilder()
    for dt in get_day_types():
        builder.button(text=f"📅 {dt}", callback_data=f"day|{category}|{dt}")
    builder.button(text="⬅️ Back", callback_data="back|cats")
    builder.adjust(1)
    return builder.as_markup()


def time_slots_keyboard(category: str, day_type: str) -> InlineKeyboardMarkup:
    """9:30-11:30, 14:30-16:30, etc."""
    builder = InlineKeyboardBuilder()
    for slot in get_time_slots(day_type):
        builder.button(text=f"🕐 {slot}", callback_data=f"slot|{category}|{day_type}|{slot}")
    builder.button(text="⬅️ Back", callback_data=f"back|day|{category}")
    builder.adjust(1)
    return builder.as_markup()


def group_names_keyboard(category: str, day_type: str = "", time_slot: str = "") -> InlineKeyboardMarkup:
    """Hunters, Assassins, Hackers."""
    builder = InlineKeyboardBuilder()
    for g in get_group_names():
        cb = f"grp|{category}|{day_type}|{time_slot}|{g}"
        builder.button(text=f"🏷 {g}", callback_data=cb)
    # back button
    if day_type and time_slot:
        builder.button(text="⬅️ Back", callback_data=f"back|slot|{category}|{day_type}")
    else:
        builder.button(text="⬅️ Back", callback_data="back|cats")
    builder.adjust(1)
    return builder.as_markup()


def sections_keyboard(category: str, day_type: str = "", time_slot: str = "", group_name: str = "") -> InlineKeyboardMarkup:
    """Section buttons for a given category."""
    builder = InlineKeyboardBuilder()
    sections = get_sections(category)
    for sec in sections:
        icon = get_section_icon(sec)
        cb = f"sec|{category}|{day_type}|{time_slot}|{group_name}|{sec}"
        builder.button(text=f"{icon} {sec}", callback_data=cb)
    # back button
    if group_name:
        if day_type and time_slot:
            builder.button(text="⬅️ Back", callback_data=f"back|grp|{category}|{day_type}|{time_slot}")
        else:
            builder.button(text="⬅️ Back", callback_data=f"back|grponly|{category}")
    else:
        builder.button(text="⬅️ Back", callback_data="back|cats")
    builder.adjust(1)
    return builder.as_markup()


def back_to_sections_keyboard(category: str, day_type: str = "", time_slot: str = "", group_name: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ Back to Sections",
        callback_data=f"backsec|{category}|{day_type}|{time_slot}|{group_name}",
    )
    builder.adjust(1)
    return builder.as_markup()


# ── ADMIN KEYBOARDS ───────────────────────────────────────────────

def adm_categories_keyboard(action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in get_categories():
        builder.button(text=cat, callback_data=f"adm|{action}|cat|{cat}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def adm_day_types_keyboard(action: str, category: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for dt in get_day_types():
        cb = f"adm|{action}|dt|{category}|{dt}" if category else f"adm|{action}|dt||{dt}"
        builder.button(text=dt, callback_data=cb)
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def adm_time_slots_keyboard(action: str, category: str, day_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in get_time_slots(day_type):
        builder.button(text=slot, callback_data=f"adm|{action}|ts|{category}|{day_type}|{slot}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def adm_group_names_keyboard(action: str, category: str = "", day_type: str = "", time_slot: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in get_group_names():
        builder.button(text=g, callback_data=f"adm|{action}|gn|{category}|{day_type}|{time_slot}|{g}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def adm_sections_keyboard(action: str, category: str, day_type: str = "", time_slot: str = "", group_name: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sec in get_sections(category):
        builder.button(
            text=sec,
            callback_data=f"adm|{action}|sec|{category}|{day_type}|{time_slot}|{group_name}|{sec}",
        )
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def adm_manage_list_keyboard(action: str, items: list, prefix: str) -> InlineKeyboardMarkup:
    """Generic keyboard for managing a list (day types, time slots, group names, categories)."""
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=item, callback_data=f"adm|{action}|{prefix}|{item}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def adm_sections_manage_keyboard(action: str, category: str) -> InlineKeyboardMarkup:
    """For add/delete/rename section — shows existing sections for a category."""
    builder = InlineKeyboardBuilder()
    for sec in get_sections(category):
        builder.button(text=sec, callback_data=f"adm|{action}|msec|{category}|{sec}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()
