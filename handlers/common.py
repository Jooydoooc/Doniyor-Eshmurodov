"""
Common handlers — /start, /help and the welcome flow for everyone.
"""

import os
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from database import upsert_user
from keyboards import levels_keyboard, groups_keyboard, sections_keyboard

router = Router(name="common")


def is_admin(user_id: int) -> bool:
    """Check if a Telegram user is the admin."""
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return False
    try:
        return int(admin_id) == user_id
    except ValueError:
        return False


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user:
        upsert_user(user.id, user.username, user.first_name)

    name = user.first_name if user and user.first_name else "student"

    # Send the permanent bottom keyboard first
    await message.answer(
        f"👋 Welcome, <b>{name}</b>! Use the buttons below to navigate.",
        reply_markup=main_menu_keyboard(),   # ← this sets the permanent buttons
    )

    # Then show the level selection as before
    await message.answer(
        "📚 Choose your <b>level</b>:",
        reply_markup=levels_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show help text. Admins see extra commands."""
    student_help = (
        "<b>📘 How to use this bot</b>\n\n"
        "1. Tap /start to open the menu.\n"
        "2. Choose your <b>level</b> (Beginner, Elementary, etc.).\n"
        "3. Choose your <b>group</b> (Hunters, Hackers, Assassins).\n"
        "4. Pick a section: Tasks, Homework, Materials, Books, "
        "Recorded Lessons, or Lesson Files.\n\n"
        "Use /menu any time to go back to the levels menu."
    )

    admin_help = (
        "\n\n<b>👑 Admin commands</b>\n"
        "/add_homework — add homework to a group\n"
        "/add_task — add a task\n"
        "/add_material — add learning material\n"
        "/add_book — add a book (PDF)\n"
        "/add_recorded_lesson — add a recorded video lesson\n"
        "/add_lesson_file — add a lesson file (Word, PPT, etc.)\n"
        "/show_content — view content for a group/section\n"
        "/delete_content — delete a content item by id\n"
        "/announcement — send an announcement to all students\n"
        "/cancel — cancel the current admin action"
    )

    text = student_help
    if message.from_user and is_admin(message.from_user.id):
        text += admin_help

    await message.answer(text)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Re-open the levels menu."""
    await message.answer(
        "📚 Choose your <b>level</b>:",
        reply_markup=levels_keyboard(),
    )


# ---------- NAVIGATION CALLBACKS (back buttons) ----------

@router.callback_query(F.data == "back|levels")
async def back_to_levels(callback: CallbackQuery) -> None:
    """Return to levels menu."""
    await callback.message.edit_text(
        "📚 Choose your <b>level</b>:",
        reply_markup=levels_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|groups|"))
async def back_to_groups(callback: CallbackQuery) -> None:
    """Return to groups menu for a level."""
    _, _, level = callback.data.split("|", 2)
    await callback.message.edit_text(
        f"📂 Level: <b>{level}</b>\n\nChoose your <b>group</b>:",
        reply_markup=groups_keyboard(level),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|sections|"))
async def back_to_sections(callback: CallbackQuery) -> None:
    """Return to sections menu for a level/group."""
    parts = callback.data.split("|")
    # parts = ["back", "sections", level, group]
    _, _, level, group = parts
    await callback.message.answer(
        f"📁 <b>{level}</b> → <b>{group}</b>\n\nChoose a section:",
        reply_markup=sections_keyboard(level, group),
    )
    await callback.answer()
    @router.message(F.text == "📚 My Level")
async def btn_my_level(message: Message) -> None:
    """Student tapped 'My Level' button."""
    await message.answer(
        "📚 Choose your <b>level</b>:",
        reply_markup=levels_keyboard(),
    )

@router.message(F.text == "ℹ️ Help")
async def btn_help(message: Message) -> None:
    """Student tapped 'Help' button."""
    await message.answer(
        "<b>📘 How to use this bot</b>\n\n"
        "1. Tap <b>📚 My Level</b> to open the menu.\n"
        "2. Choose your level, then your group.\n"
        "3. Pick a section to view content.\n\n"
        "Tap <b>📣 Announcements</b> to see the latest news."
    )

@router.message(F.text == "📣 Announcements")
async def btn_announcements(message: Message) -> None:
    """Show the latest announcement."""
    from database import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT text, created_at FROM announcements ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        await message.answer("📭 No announcements yet.")
    else:
        await message.answer(f"📣 <b>Latest Announcement</b>\n\n{row['text']}")
