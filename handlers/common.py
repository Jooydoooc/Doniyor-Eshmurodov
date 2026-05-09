"""
Common handlers — /start, /help, /menu, student navigation callbacks,
and bottom reply keyboard button handlers.
"""

import os
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from database import upsert_user, get_latest_announcement
from keyboards import (
    main_reply_keyboard, categories_keyboard,
    day_types_keyboard, time_slots_keyboard,
    group_names_keyboard, sections_keyboard,
    back_to_sections_keyboard,
)

router = Router(name="common")

GROUPS_CATEGORY = "Groups"
UNIVERSAL_CATEGORY = "Universal"


def is_admin(user_id: int) -> bool:
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
    admin_note = ""
    if user and is_admin(user.id):
        admin_note = "\n\n👑 You are the <b>admin</b>. Send /help to see all commands."
    await message.answer(
        "👋 Welcome, <b>" + name + "</b>!\n\n"
        "Use the buttons below to navigate your content." + admin_note,
        reply_markup=main_reply_keyboard(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer("📋 Choose a category:", reply_markup=categories_keyboard())


# ── BOTTOM MENU BUTTONS ───────────────────────────────────────────

@router.message(F.text == "⚡ Groups")
async def btn_groups(message: Message) -> None:
    await message.answer(
        "👥 <b>Groups</b>\n\nChoose day type:",
        reply_markup=day_types_keyboard(GROUPS_CATEGORY),
    )


@router.message(F.text == "🔮 Universal")
async def btn_universal(message: Message) -> None:
    await message.answer(
        "🌐 <b>Universal</b>\n\nChoose your group:",
        reply_markup=group_names_keyboard(UNIVERSAL_CATEGORY),
    )


@router.message(F.text == "🎯 Mock Tests")
async def btn_mock_tests(message: Message) -> None:
    await message.answer(
        "📋 <b>Mock Tests</b>\n\nChoose a section:",
        reply_markup=sections_keyboard("Mock Tests"),
    )


@router.message(F.text == "🚀 Channel")
async def btn_channel(message: Message) -> None:
    await message.answer(
        "📢 <b>Telegram Channel</b>\n\nChoose a section:",
        reply_markup=sections_keyboard("Telegram Channel"),
    )


@router.message(F.text == "💬 Announcements")
async def btn_announcements(message: Message) -> None:
    text = get_latest_announcement()
    if not text:
        await message.answer("📭 No announcements yet.")
    else:
        await message.answer("📣 <b>Latest Announcement</b>\n\n" + text)


# ── /help ─────────────────────────────────────────────────────────

@router.message(F.text == "ℹ️ Help")
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>📘 How to use this bot</b>\n\n"
        "Use the buttons at the bottom:\n\n"
        "👥 <b>Groups</b> — Odd/Even days → time slot → group → section\n"
        "🌐 <b>Universal</b> — shared content → group → section\n"
        "📋 <b>Mock Tests</b> — test files, answer keys, results\n"
        "📢 <b>Channel</b> — Telegram channel links and resources\n"
        "📣 <b>Announcements</b> — latest announcement from your teacher"
    )
    if message.from_user and is_admin(message.from_user.id):
        text += (
            "\n\n<b>👑 Admin commands</b>\n"
            "<b>Content:</b> /add_content · /show_content · /delete_content\n"
            "<b>Categories:</b> /add_category · /delete_category · /rename_category · /list_categories\n"
            "<b>Day Types:</b> /add_day_type · /delete_day_type · /rename_day_type · /list_day_types\n"
            "<b>Time Slots:</b> /add_time_slot · /delete_time_slot · /rename_time_slot · /list_time_slots\n"
            "<b>Groups:</b> /add_group · /delete_group · /rename_group · /list_groups\n"
            "<b>Sections:</b> /add_section · /delete_section · /rename_section · /list_sections\n"
            "<b>Other:</b> /announcement · /cancel"
        )
    await message.answer(text)


# ── CATEGORY CALLBACK ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("cat|"))
async def on_category(callback: CallbackQuery) -> None:
    _, category = callback.data.split("|", 1)
    if category == GROUPS_CATEGORY:
        await callback.message.edit_text(
            "👥 <b>" + category + "</b>\n\nChoose day type:",
            reply_markup=day_types_keyboard(category),
        )
    elif category == UNIVERSAL_CATEGORY:
        await callback.message.edit_text(
            "🌐 <b>" + category + "</b>\n\nChoose your group:",
            reply_markup=group_names_keyboard(category),
        )
    else:
        await callback.message.edit_text(
            "📌 <b>" + category + "</b>\n\nChoose a section:",
            reply_markup=sections_keyboard(category),
        )
    await callback.answer()


# ── GROUPS FLOW ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("day|"))
async def on_day_type(callback: CallbackQuery) -> None:
    _, category, day_type = callback.data.split("|", 2)
    await callback.message.edit_text(
        "👥 <b>" + category + "</b> › " + day_type + "\n\nChoose a time slot:",
        reply_markup=time_slots_keyboard(category, day_type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("slot|"))
async def on_time_slot(callback: CallbackQuery) -> None:
    _, category, day_type, time_slot = callback.data.split("|", 3)
    await callback.message.edit_text(
        "👥 <b>" + category + "</b> › " + day_type + " › " + time_slot + "\n\nChoose your group:",
        reply_markup=group_names_keyboard(category, day_type, time_slot),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("grp|"))
async def on_group_name(callback: CallbackQuery) -> None:
    _, category, day_type, time_slot, group_name = callback.data.split("|", 4)
    await callback.message.edit_text(
        "🏷 <b>" + group_name + "</b>\n\nChoose a section:",
        reply_markup=sections_keyboard(category, day_type, time_slot, group_name),
    )
    await callback.answer()


# ── SECTION → CONTENT ────────────────────────────────────────────

@router.callback_query(F.data.startswith("sec|"))
async def on_section(callback: CallbackQuery) -> None:
    parts = callback.data.split("|")
    _, category, day_type, time_slot, group_name, section = parts

    from database import get_content
    rows = get_content(
        category=category,
        section=section,
        day_type=day_type or None,
        time_slot=time_slot or None,
        group_name=group_name or None,
    )

    parts_display = ["<b>" + category + "</b>"]
    if day_type:
        parts_display.append(day_type)
    if time_slot:
        parts_display.append(time_slot)
    if group_name:
        parts_display.append("<b>" + group_name + "</b>")
    parts_display.append("📌 " + section)
    header = " › ".join(parts_display)

    if not rows:
        await callback.message.answer(
            header + "\n\n<i>No content yet. Check back later.</i>",
            reply_markup=back_to_sections_keyboard(category, day_type, time_slot, group_name),
        )
        await callback.answer()
        return

    await callback.message.answer(header + "\n\n" + str(len(rows)) + " item(s):")
    for row in rows:
        await send_content_item(callback.bot, callback.message.chat.id, row)
    await callback.message.answer(
        "✅ End of section.",
        reply_markup=back_to_sections_keyboard(category, day_type, time_slot, group_name),
    )
    await callback.answer()


async def send_content_item(bot, chat_id: int, row) -> None:
    text = row["text"]
    file_id = row["file_id"]
    file_type = row["file_type"]
    caption = row["caption"]
    body_parts = []
    if text:
        body_parts.append(text)
    if caption and caption != text:
        body_parts.append(caption)
    body = "\n\n".join(body_parts) if body_parts else None
    if not file_id:
        await bot.send_message(chat_id, body or "(empty)")
        return
    if file_type == "photo":
        await bot.send_photo(chat_id, file_id, caption=body)
    elif file_type == "video":
        await bot.send_video(chat_id, file_id, caption=body)
    elif file_type == "audio":
        await bot.send_audio(chat_id, file_id, caption=body)
    elif file_type == "voice":
        await bot.send_voice(chat_id, file_id, caption=body)
    elif file_type == "video_note":
        await bot.send_video_note(chat_id, file_id)
        if body:
            await bot.send_message(chat_id, body)
    else:
        await bot.send_document(chat_id, file_id, caption=body)


# ── BACK BUTTONS ─────────────────────────────────────────────────

@router.callback_query(F.data == "back|cats")
async def back_to_cats(callback: CallbackQuery) -> None:
    await callback.message.edit_text("📋 Choose a category:", reply_markup=categories_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("back|day|"))
async def back_to_day(callback: CallbackQuery) -> None:
    _, _, category = callback.data.split("|", 2)
    await callback.message.edit_text(
        "👥 <b>" + category + "</b>\n\nChoose day type:",
        reply_markup=day_types_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|slot|"))
async def back_to_slot(callback: CallbackQuery) -> None:
    _, _, category, day_type = callback.data.split("|", 3)
    await callback.message.edit_text(
        "👥 <b>" + category + "</b> › " + day_type + "\n\nChoose a time slot:",
        reply_markup=time_slots_keyboard(category, day_type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|grp|"))
async def back_to_grp(callback: CallbackQuery) -> None:
    parts = callback.data.split("|")
    _, _, category, day_type, time_slot = parts
    await callback.message.edit_text(
        "👥 <b>" + category + "</b> › " + day_type + " › " + time_slot + "\n\nChoose your group:",
        reply_markup=group_names_keyboard(category, day_type, time_slot),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|grponly|"))
async def back_to_grp_only(callback: CallbackQuery) -> None:
    _, _, category = callback.data.split("|", 2)
    await callback.message.edit_text(
        "🌐 <b>" + category + "</b>\n\nChoose your group:",
        reply_markup=group_names_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("backsec|"))
async def back_to_sections(callback: CallbackQuery) -> None:
    parts = callback.data.split("|")
    _, category, day_type, time_slot, group_name = parts
    await callback.message.answer(
        "📌 Choose a section:",
        reply_markup=sections_keyboard(category, day_type, time_slot, group_name),
    )
    await callback.answer()
