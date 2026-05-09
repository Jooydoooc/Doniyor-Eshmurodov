"""
Admin handlers — only the admin (ADMIN_ID from .env) can use these.

Flow for adding content (e.g. /add_homework):
  1. Admin runs the command.
  2. Bot asks: which level? (inline buttons)
  3. Admin picks level. Bot asks: which group? (inline buttons)
  4. Admin picks group. Bot asks: send the content now.
  5. Admin sends a message — text, photo, video, document, audio, voice.
     The bot saves the message's file_id (if any) and text/caption.
  6. Bot confirms and exits the flow.

Flow for /show_content and /delete_content is similar but ends with
showing a list and (for delete) accepting an id.
"""

import os
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import (
    add_content,
    add_announcement,
    delete_content,
    get_all_user_ids,
    get_content,
    get_content_by_id,
)
from keyboards import (
    admin_groups_keyboard,
    admin_levels_keyboard,
    admin_sections_keyboard,
)

router = Router(name="admin")


# ---------- ADMIN CHECK ----------

def is_admin(user_id: int) -> bool:
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return False
    try:
        return int(admin_id) == user_id
    except ValueError:
        return False


# Map command names to section names
SECTION_BY_COMMAND = {
    "add_homework": "Homework",
    "add_task": "Tasks",
    "add_material": "Materials",
    "add_book": "Books",
    "add_recorded_lesson": "Recorded Lessons",
    "add_lesson_file": "Lesson Files",
}


# ---------- FSM STATES ----------

class AddContent(StatesGroup):
    waiting_for_level = State()
    waiting_for_group = State()
    waiting_for_content = State()


class ShowContent(StatesGroup):
    waiting_for_level = State()
    waiting_for_group = State()
    waiting_for_section = State()


class DeleteContent(StatesGroup):
    waiting_for_id = State()


class Announcement(StatesGroup):
    waiting_for_text = State()


# ---------- /cancel ----------

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Cancel any active admin flow."""
    if not is_admin(message.from_user.id):
        return
    current = await state.get_state()
    if current is None:
        await message.answer("Nothing to cancel.")
        return
    await state.clear()
    await message.answer("✅ Cancelled.")


# ---------- ADD-CONTENT COMMANDS ----------

@router.message(Command(commands=list(SECTION_BY_COMMAND.keys())))
async def cmd_add_content(message: Message, state: FSMContext) -> None:
    """Entry point for all /add_* commands."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return

    # Extract command name without leading '/'
    command = message.text.split()[0].lstrip("/").split("@")[0]
    section = SECTION_BY_COMMAND.get(command)
    if not section:
        return

    await state.clear()
    await state.update_data(section=section, action="add")
    await state.set_state(AddContent.waiting_for_level)
    await message.answer(
        f"📌 Adding new <b>{section}</b>.\n\nChoose a <b>level</b>:",
        reply_markup=admin_levels_keyboard("add"),
    )


@router.callback_query(
    StateFilter(AddContent.waiting_for_level),
    F.data.startswith("adm|add|lvl|"),
)
async def admin_pick_level_for_add(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level = callback.data.split("|", 3)
    await state.update_data(level=level)
    await state.set_state(AddContent.waiting_for_group)
    await callback.message.edit_text(
        f"📂 Level: <b>{level}</b>\n\nChoose a <b>group</b>:",
        reply_markup=admin_groups_keyboard("add", level),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AddContent.waiting_for_group),
    F.data.startswith("adm|add|grp|"),
)
async def admin_pick_group_for_add(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    data = await state.get_data()
    section = data.get("section")
    await state.update_data(group=group)
    await state.set_state(AddContent.waiting_for_content)
    await callback.message.edit_text(
        f"📥 Now send the <b>{section}</b> for <b>{level} → {group}</b>.\n\n"
        "You can send:\n"
        "• plain text\n"
        "• a PDF, Word file, or any document\n"
        "• a photo (with optional caption)\n"
        "• a video, audio, or voice message\n\n"
        "Send /cancel to abort."
    )
    await callback.answer()


@router.message(StateFilter(AddContent.waiting_for_content))
async def admin_receive_content(message: Message, state: FSMContext) -> None:
    """Receive the actual content from the admin and save it."""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    level = data.get("level")
    group = data.get("group")
    section = data.get("section")

    # Detect what kind of content was sent
    file_id = None
    file_type = None
    text = None
    caption = message.caption

    if message.photo:
        # photo is a list of sizes; the largest is the last one
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"
    elif message.video_note:
        file_id = message.video_note.file_id
        file_type = "video_note"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.text:
        text = message.text
    else:
        await message.answer(
            "⚠️ Unsupported content type. Please send text, a photo, video, audio, "
            "voice message, or document. Or send /cancel."
        )
        return

    new_id = add_content(
        level=level,
        group_name=group,
        section=section,
        text=text,
        file_id=file_id,
        file_type=file_type,
        caption=caption,
    )

    await state.clear()
    summary = (
        f"✅ Saved!\n\n"
        f"<b>ID:</b> {new_id}\n"
        f"<b>Level:</b> {level}\n"
        f"<b>Group:</b> {group}\n"
        f"<b>Section:</b> {section}\n"
        f"<b>Type:</b> {file_type or 'text'}"
    )
    await message.answer(summary)


# ---------- /show_content ----------

@router.message(Command("show_content"))
async def cmd_show_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    await state.clear()
    await state.set_state(ShowContent.waiting_for_level)
    await message.answer(
        "🔎 Choose a <b>level</b> to view content:",
        reply_markup=admin_levels_keyboard("show"),
    )


@router.callback_query(
    StateFilter(ShowContent.waiting_for_level),
    F.data.startswith("adm|show|lvl|"),
)
async def admin_pick_level_for_show(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level = callback.data.split("|", 3)
    await state.update_data(level=level)
    await state.set_state(ShowContent.waiting_for_group)
    await callback.message.edit_text(
        f"📂 Level: <b>{level}</b>\n\nChoose a <b>group</b>:",
        reply_markup=admin_groups_keyboard("show", level),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(ShowContent.waiting_for_group),
    F.data.startswith("adm|show|grp|"),
)
async def admin_pick_group_for_show(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.update_data(group=group)
    await state.set_state(ShowContent.waiting_for_section)
    await callback.message.edit_text(
        f"📁 <b>{level} → {group}</b>\n\nChoose a <b>section</b>:",
        reply_markup=admin_sections_keyboard("show", level, group),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(ShowContent.waiting_for_section),
    F.data.startswith("adm|show|sec|"),
)
async def admin_pick_section_for_show(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    # parts = ["adm","show","sec",level,group,section]
    _, _, _, level, group, section = parts
    await state.clear()

    rows = get_content(level, group, section)
    if not rows:
        await callback.message.edit_text(
            f"📭 No content found for <b>{level} → {group} → {section}</b>."
        )
        await callback.answer()
        return

    lines = [f"📋 <b>{level} → {group} → {section}</b>\n"]
    for row in rows:
        kind = row["file_type"] or "text"
        preview = (row["text"] or row["caption"] or "")[:60]
        if preview:
            preview = preview.replace("\n", " ")
            preview = f" — {preview}"
        lines.append(f"• <b>ID {row['id']}</b> [{kind}]{preview}")

    lines.append("\nTo delete an item, run /delete_content")
    await callback.message.edit_text("\n".join(lines))
    await callback.answer()


# ---------- /delete_content ----------

@router.message(Command("delete_content"))
async def cmd_delete_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    await state.clear()
    await state.set_state(DeleteContent.waiting_for_id)
    await message.answer(
        "🗑 Send the <b>ID</b> of the content item to delete.\n"
        "(Use /show_content first to find IDs.)\n\n"
        "Send /cancel to abort."
    )


@router.message(StateFilter(DeleteContent.waiting_for_id))
async def admin_delete_by_id(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("⚠️ Please send a numeric ID, or /cancel.")
        return

    content_id = int(text)
    row = get_content_by_id(content_id)
    if not row:
        await message.answer(f"❌ No content found with ID {content_id}.")
        await state.clear()
        return

    deleted = delete_content(content_id)
    await state.clear()
    if deleted:
        await message.answer(
            f"✅ Deleted ID {content_id} "
            f"({row['level']} → {row['group_name']} → {row['section']})."
        )
    else:
        await message.answer(f"❌ Could not delete ID {content_id}.")


# ---------- /announcement ----------

@router.message(Command("announcement"))
async def cmd_announcement(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    await state.clear()
    await state.set_state(Announcement.waiting_for_text)
    await message.answer(
        "📣 Send the announcement text to broadcast to all students.\n"
        "Send /cancel to abort."
    )


@router.message(StateFilter(Announcement.waiting_for_text))
async def admin_send_announcement(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if not message.text:
        await message.answer("⚠️ Please send plain text, or /cancel.")
        return

    text = message.text.strip()
    add_announcement(text)
    user_ids = get_all_user_ids()
    await state.clear()

    sent = 0
    failed = 0
    body = f"📣 <b>Announcement</b>\n\n{text}"
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, body)
            sent += 1
        except Exception:
            # User may have blocked the bot, deleted account, etc.
            failed += 1

    await message.answer(
        f"✅ Announcement sent.\nDelivered: {sent}\nFailed: {failed}"
    )


# ---------- CANCEL FROM INLINE BUTTON ----------

@router.callback_query(F.data == "adm|cancel")
async def admin_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("✅ Cancelled.")
    await callback.answer()
