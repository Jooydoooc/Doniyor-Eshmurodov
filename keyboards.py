"""
Keyboard module — fully dynamic groups and sections from database.
"""

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import LEVELS, get_groups, get_sections, get_section_icon


def levels_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in LEVELS:
        builder.button(text=level, callback_data=f"level|{level}")
    builder.adjust(1)
    return builder.as_markup()


def groups_keyboard(level: str) -> InlineKeyboardMarkup:
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
    sections = get_sections(level)
    if sections:
        for section in sections:
            icon = get_section_icon(section)
            builder.button(
                text=f"{icon} {section}",
                callback_data=f"section|{level}|{group}|{section}",
            )
    else:
        builder.button(text="⚠️ No sections yet", callback_data="noop")
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


# ── ADMIN KEYBOARDS ──

def admin_levels_keyboard(action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in LEVELS:
        builder.button(text=level, callback_data=f"adm|{action}|lvl|{level}")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def admin_groups_keyboard(action: str, level: str) -> InlineKeyboardMarkup:
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


def admin_sections_keyboard(action: str, level: str, group: str = "") -> InlineKeyboardMarkup:
    """Used in show/delete content flows — shows sections for a level."""
    builder = InlineKeyboardBuilder()
    sections = get_sections(level)
    if sections:
        for section in sections:
            cb = (
                f"adm|{action}|sec|{level}|{group}|{section}"
                if group
                else f"adm|{action}|sec|{level}||{section}"
            )
            builder.button(text=section, callback_data=cb)
    else:
        builder.button(text="⚠️ No sections for this level", callback_data="noop")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


def admin_sections_manage_keyboard(action: str, level: str) -> InlineKeyboardMarkup:
    """Used in add/delete/rename section flows — shows existing sections."""
    builder = InlineKeyboardBuilder()
    sections = get_sections(level)
    if sections:
        for section in sections:
            builder.button(
                text=section,
                callback_data=f"adm|{action}|msec|{level}|{section}",
            )
    else:
        builder.button(text="⚠️ No sections yet", callback_data="noop")
    builder.button(text="❌ Cancel", callback_data="adm|cancel")
    builder.adjust(1)
    return builder.as_markup()


# ── REPLY KEYBOARD ──

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
