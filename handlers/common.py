"""
Common handlers — /start, /help, /menu, student navigation callbacks.

Navigation flow:
  Groups:           cat → day_type → time_slot → group_name → section → content
  Universal:        cat → group_name → section → content
  Mock Tests:       cat → section → content
  Telegram Channel: cat → section → content
  Custom category:  cat → section → content
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


# ── /start ───────────────────────────────────────────────────────

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
        f"👋 Welcome, <b>{name}</b>!\n\n"
        "Use the <b>Menu</b> button below or tap /menu to browse content." + admin_note,
        reply_markup=main_reply_keyboard(),
    )
    await message.answer("📋 Choose a category:", reply_markup=categories_keyboard())


@router.message(Command("menu"))
@router.message(F.text == "📋 Menu")
async def cmd_menu(message: Message) -> None:
    await message.answer("📋 Choose a category:", reply_markup=categories_keyboard())


@router.message(F.text == "ℹ️ Help")
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>📘 How to use this bot</b>\n\n"
        "1. Tap <b>📋 Menu</b> to open the main menu.\n"
        "2. Choose a category: Groups, Universal, Mock Tests, etc.\n"
        "3. For <b>Groups</b>: pick Odd/Even days → time slot → group name → section.\n"
        "4. For other categories: pick a section directly.\n"
        "5. The bot will send all content for that section.\n\n"
        "Tap <b>📣 Announcements</b> to see the latest announcement."
    )
    if message.from_user and is_admin(message.from_user.id):
        text += (
            "\n\n<b>👑 Admin commands</b>\n"
            "<b>— Content —</b>\n"
            "/add_content — add content to any category/group/section\n"
            "/show_content — view saved content\n"
            "/delete_content — delete a content item by ID\n\n"
            "<b>— Categories —</b>\n"
            "/add_category · /delete_category · /rename_category · /list_categories\n\n"
            "<b>— Day Types —</b>\n"
            "/add_day_type · /delete_day_type · /rename_day_type · /list_day_types\n\n"
            "<b>— Time Slots —</b>\n"
            "/add_time_slot · /delete_time_slot · /rename_time_slot · /list_time_slots\n\n"
            "<b>— Group Names —</b>\n"
            "/add_group · /delete_group · /rename_group · /list_groups\n\n"
            "<b>— Sections —</b>\n"
            "/add_section · /delete_section · /rename_section · /list_sections\n\n"
            "<b>— Other —</b>\n"
            "/announcement · /cancel"
        )
    await message.answer(text)


@router.message(F.text == "📣 Announcements")
async def btn_announcements(message: Message) -> None:
    text = get_latest_announcement()
    if not text:
        await message.answer("📭 No announcements yet.")
    else:
        await message.answer(f"📣 <b>Latest Announcement</b>\n\n{text}")


# ── CATEGORY SELECTED ────────────────────────────────────────────

@router.callback_query(F.data.startswith("cat|"))
async def on_category(callback: CallbackQuery) -> None:
    _, category = callback.data.split("|", 1)

    if category == GROUPS_CATEGORY:
        await callback.message.edit_text(
            f"👥 <b>{category}</b>\n\nChoose day type:",
            reply_markup=day_types_keyboard(category),
        )
    elif category == UNIVERSAL_CATEGORY:
        await callback.message.edit_text(
            f"🌐 <b>{category}</b>\n\nChoose your group:",
            reply_markup=group_names_keyboard(category),
        )
    else:
        # Mock Tests, Telegram Channel, custom categories → go straight to sections
        await callback.message.edit_text(
            f"📌 <b>{category}</b>\n\nChoose a section:",
            reply_markup=sections_keyboard(category),
        )
    await callback.answer()


# ── GROUPS FLOW ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("day|"))
async def on_day_type(callback: CallbackQuery) -> None:
    _, category, day_type = callback.data.split("|", 2)
    await callback.message.edit_text(
        f"👥 <b>{category}</b> › {day_type}\n\nChoose a time slot:",
        reply_markup=time_slots_keyboard(category, day_type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("slot|"))
async def on_time_slot(callback: CallbackQuery) -> None:
    _, category, day_type, time_slot = callback.data.split("|", 3)
    await callback.message.edit_text(
        f"👥 <b>{category}</b> › {day_type} › {time_slot}\n\nChoose your group:",
        reply_markup=group_names_keyboard(category, day_type, time_slot),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("grp|"))
async def on_group_name(callback: CallbackQuery) -> None:
    _, category, day_type, time_slot, group_name = callback.data.split("|", 4)
    await callback.message.edit_text(
        f"🏷 <b>{group_name}</b>\n\nChoose a section:",
        reply_markup=sections_keyboard(category, day_type, time_slot, group_name),
    )
    await callback.answer()


# ── SECTION SELECTED → DELIVER CONTENT ───────────────────────────

@router.callback_query(F.data.startswith("sec|"))
async def on_section(callback: CallbackQuery) -> None:
    parts = callback.data.split("|")
    # parts: ["sec", category, day_type, time_slot, group_name, section]
    _, category, day_type, time_slot, group_name, section = parts

    from database import get_content
    rows = get_content(
        category=category,
        section=section,
        day_type=day_type or None,
        time_slot=time_slot or None,
        group_name=group_name or None,
    )

    # Build header
    parts_display = [f"<b>{category}</b>"]
    if day_type:
        parts_display.append(day_type)
    if time_slot:
        parts_display.append(time_slot)
    if group_name:
        parts_display.append(f"<b>{group_name}</b>")
    parts_display.append(f"📌 {section}")
    header = " › ".join(parts_display)

    if not rows:
        await callback.message.answer(
            f"{header}\n\n<i>No content yet. Please check back later.</i>",
            reply_markup=back_to_sections_keyboard(category, day_type, time_slot, group_name),
        )
        await callback.answer()
        return

    await callback.message.answer(f"{header}\n\n{len(rows)} item(s):")

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
        f"👥 <b>{category}</b>\n\nChoose day type:",
        reply_markup=day_types_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|slot|"))
async def back_to_slot(callback: CallbackQuery) -> None:
    _, _, category, day_type = callback.data.split("|", 3)
    await callback.message.edit_text(
        f"👥 <b>{category}</b> › {day_type}\n\nChoose a time slot:",
        reply_markup=time_slots_keyboard(category, day_type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|grp|"))
async def back_to_grp(callback: CallbackQuery) -> None:
    parts = callback.data.split("|")
    _, _, category, day_type, time_slot = parts
    await callback.message.edit_text(
        f"👥 <b>{category}</b> › {day_type} › {time_slot}\n\nChoose your group:",
        reply_markup=group_names_keyboard(category, day_type, time_slot),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back|grponly|"))
async def back_to_grp_only(callback: CallbackQuery) -> None:
    _, _, category = callback.data.split("|", 2)
    await callback.message.edit_text(
        f"🌐 <b>{category}</b>\n\nChoose your group:",
        reply_markup=group_names_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("backsec|"))
async def back_to_sections(callback: CallbackQuery) -> None:
    parts = callback.data.split("|")
    _, category, day_type, time_slot, group_name = parts
    await callback.message.answer(
        f"📌 Choose a section:",
        reply_markup=sections_keyboard(category, day_type, time_slot, group_name),
    )
    await callback.answer()
