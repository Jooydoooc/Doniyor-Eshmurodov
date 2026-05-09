"""
Student handlers — let students navigate levels, groups, sections,
and view content.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_content, upsert_user
from keyboards import (
    groups_keyboard,
    sections_keyboard,
    back_to_sections_keyboard,
)

router = Router(name="student")


# ---------- LEVEL SELECTED ----------

@router.callback_query(F.data.startswith("level|"))
async def on_level_selected(callback: CallbackQuery) -> None:
    """Student picked a level → show groups."""
    if callback.from_user:
        upsert_user(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
        )

    _, level = callback.data.split("|", 1)
    await callback.message.edit_text(
        f"📂 Level: <b>{level}</b>\n\nChoose your <b>group</b>:",
        reply_markup=groups_keyboard(level),
    )
    await callback.answer()


# ---------- GROUP SELECTED ----------

@router.callback_query(F.data.startswith("group|"))
async def on_group_selected(callback: CallbackQuery) -> None:
    """Student picked a group → show sections."""
    _, level, group = callback.data.split("|", 2)
    await callback.message.edit_text(
        f"📁 <b>{level}</b> → <b>{group}</b>\n\nChoose a section:",
        reply_markup=sections_keyboard(level, group),
    )
    await callback.answer()


# ---------- SECTION SELECTED ----------

@router.callback_query(F.data.startswith("section|"))
async def on_section_selected(callback: CallbackQuery) -> None:
    """Student picked a section → deliver all content for that section."""
    _, level, group, section = callback.data.split("|", 3)

    rows = get_content(level, group, section)

    header = f"📌 <b>{section}</b> for <b>{level}</b> → <b>{group}</b>"

    if not rows:
        await callback.message.answer(
            f"{header}\n\n<i>No content has been added yet. Please check back later.</i>",
            reply_markup=back_to_sections_keyboard(level, group),
        )
        await callback.answer()
        return

    await callback.message.answer(f"{header}\n\nShowing {len(rows)} item(s):")

    bot = callback.bot
    chat_id = callback.message.chat.id

    # Send each item one by one
    for row in rows:
        await send_content_item(bot, chat_id, row)

    # Final back button after all content
    await callback.message.answer(
        "✅ End of section.",
        reply_markup=back_to_sections_keyboard(level, group),
    )
    await callback.answer()


async def send_content_item(bot, chat_id: int, row) -> None:
    """
    Send a single content row to a chat.
    Handles text-only, photo, document, audio, video — based on file_type.
    """
    text = row["text"]
    file_id = row["file_id"]
    file_type = row["file_type"]
    caption = row["caption"]

    # Compose the caption / text body
    body_parts = []
    if text:
        body_parts.append(text)
    if caption and caption != text:
        body_parts.append(caption)
    body = "\n\n".join(body_parts) if body_parts else None

    if not file_id:
        # Text-only content
        await bot.send_message(chat_id, body or "(empty)")
        return

    # File content — send the right method based on file_type
    if file_type == "photo":
        await bot.send_photo(chat_id, file_id, caption=body)
    elif file_type == "video":
        await bot.send_video(chat_id, file_id, caption=body)
    elif file_type == "audio":
        await bot.send_audio(chat_id, file_id, caption=body)
    elif file_type == "voice":
        await bot.send_voice(chat_id, file_id, caption=body)
    elif file_type == "document":
        await bot.send_document(chat_id, file_id, caption=body)
    elif file_type == "video_note":
        await bot.send_video_note(chat_id, file_id)
        if body:
            await bot.send_message(chat_id, body)
    else:
        # Fallback: send as a document
        await bot.send_document(chat_id, file_id, caption=body)
