"""
Admin handlers — all admin commands.
New in this version:
  /add_group    — add a group to a level
  /delete_group — delete a group (and all its content)
  /rename_group — rename a group
  /list_groups  — see all groups per level
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
    add_group,
    delete_group,
    rename_group,
    get_all_groups,
    get_groups,
    delete_content,
    get_all_user_ids,
    get_content,
    get_content_by_id,
    LEVELS,
)
from keyboards import (
    admin_groups_keyboard,
    admin_levels_keyboard,
    admin_sections_keyboard,
)

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return False
    try:
        return int(admin_id) == user_id
    except ValueError:
        return False


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


class AddGroup(StatesGroup):
    waiting_for_level = State()
    waiting_for_name = State()


class DeleteGroup(StatesGroup):
    waiting_for_level = State()
    waiting_for_group = State()


class RenameGroup(StatesGroup):
    waiting_for_level = State()
    waiting_for_group = State()
    waiting_for_new_name = State()


# ---------- /cancel ----------

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if await state.get_state() is None:
        await message.answer("Nothing to cancel.")
        return
    await state.clear()
    await message.answer("✅ Cancelled.")


# ---------- /list_groups ----------

@router.message(Command("list_groups"))
async def cmd_list_groups(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    rows = get_all_groups()
    if not rows:
        await message.answer("No groups found.")
        return
    current_level = None
    lines = ["📋 <b>All groups:</b>\n"]
    for row in rows:
        if row["level"] != current_level:
            current_level = row["level"]
            lines.append(f"\n<b>{current_level}</b>")
        lines.append(f"  • {row['group_name']}")
    await message.answer("\n".join(lines))


# ---------- /add_group ----------

@router.message(Command("add_group"))
async def cmd_add_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(AddGroup.waiting_for_level)
    await message.answer(
        "➕ <b>Add a new group</b>\n\nChoose the <b>level</b> for the new group:",
        reply_markup=admin_levels_keyboard("addgrp"),
    )


@router.callback_query(
    StateFilter(AddGroup.waiting_for_level),
    F.data.startswith("adm|addgrp|lvl|"),
)
async def admin_add_group_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level = callback.data.split("|", 3)
    await state.update_data(level=level)
    await state.set_state(AddGroup.waiting_for_name)

    existing = get_groups(level)
    existing_text = ", ".join(existing) if existing else "none yet"
    await callback.message.edit_text(
        f"➕ Adding group to <b>{level}</b>\n\n"
        f"Current groups: <i>{existing_text}</i>\n\n"
        f"Type the <b>name</b> of the new group and send it:\n"
        f"(e.g. Warriors, Champions, Rookies)"
    )
    await callback.answer()


@router.message(StateFilter(AddGroup.waiting_for_name))
async def admin_add_group_receive_name(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Please send a group name, or /cancel.")
        return

    data = await state.get_data()
    level = data.get("level")
    success = add_group(level, name)
    await state.clear()

    if success:
        await message.answer(
            f"✅ Group <b>{name}</b> added to <b>{level}</b>!\n\n"
            f"Students in {level} will now see this group."
        )
    else:
        await message.answer(
            f"⚠️ Group <b>{name}</b> already exists in <b>{level}</b>."
        )


# ---------- /delete_group ----------

@router.message(Command("delete_group"))
async def cmd_delete_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(DeleteGroup.waiting_for_level)
    await message.answer(
        "🗑 <b>Delete a group</b>\n\n"
        "⚠️ This will also delete ALL content in that group.\n\n"
        "Choose the <b>level</b>:",
        reply_markup=admin_levels_keyboard("delgrp"),
    )


@router.callback_query(
    StateFilter(DeleteGroup.waiting_for_level),
    F.data.startswith("adm|delgrp|lvl|"),
)
async def admin_delete_group_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level = callback.data.split("|", 3)
    await state.update_data(level=level)
    await state.set_state(DeleteGroup.waiting_for_group)
    await callback.message.edit_text(
        f"🗑 <b>{level}</b>\n\nChoose the <b>group to delete</b>:",
        reply_markup=admin_groups_keyboard("delgrp", level),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(DeleteGroup.waiting_for_group),
    F.data.startswith("adm|delgrp|grp|"),
)
async def admin_delete_group_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.clear()
    success = delete_group(level, group)
    if success:
        await callback.message.edit_text(
            f"✅ Group <b>{group}</b> deleted from <b>{level}</b>.\n"
            f"All content in that group was also removed."
        )
    else:
        await callback.message.edit_text(
            f"❌ Could not find group <b>{group}</b> in <b>{level}</b>."
        )
    await callback.answer()


# ---------- /rename_group ----------

@router.message(Command("rename_group"))
async def cmd_rename_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(RenameGroup.waiting_for_level)
    await message.answer(
        "✏️ <b>Rename a group</b>\n\nChoose the <b>level</b>:",
        reply_markup=admin_levels_keyboard("rengrp"),
    )


@router.callback_query(
    StateFilter(RenameGroup.waiting_for_level),
    F.data.startswith("adm|rengrp|lvl|"),
)
async def admin_rename_group_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level = callback.data.split("|", 3)
    await state.update_data(level=level)
    await state.set_state(RenameGroup.waiting_for_group)
    await callback.message.edit_text(
        f"✏️ <b>{level}</b>\n\nChoose the <b>group to rename</b>:",
        reply_markup=admin_groups_keyboard("rengrp", level),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(RenameGroup.waiting_for_group),
    F.data.startswith("adm|rengrp|grp|"),
)
async def admin_rename_group_pick_group(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.update_data(level=level, old_name=group)
    await state.set_state(RenameGroup.waiting_for_new_name)
    await callback.message.edit_text(
        f"✏️ Renaming <b>{group}</b> in <b>{level}</b>\n\n"
        f"Send the <b>new name</b> for this group:"
    )
    await callback.answer()


@router.message(StateFilter(RenameGroup.waiting_for_new_name))
async def admin_rename_group_receive_name(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("⚠️ Please send a name, or /cancel.")
        return
    data = await state.get_data()
    level = data.get("level")
    old_name = data.get("old_name")
    success = rename_group(level, old_name, new_name)
    await state.clear()
    if success:
        await message.answer(
            f"✅ Group renamed!\n\n"
            f"<b>{old_name}</b> → <b>{new_name}</b> in <b>{level}</b>\n\n"
            f"All content has been moved to the new name automatically."
        )
    else:
        await message.answer(
            f"❌ Could not rename. Either <b>{old_name}</b> doesn't exist "
            f"or <b>{new_name}</b> already exists in <b>{level}</b>."
        )


# ---------- ADD CONTENT COMMANDS ----------

@router.message(Command(commands=list(SECTION_BY_COMMAND.keys())))
async def cmd_add_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
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
        f"📥 Send the <b>{section}</b> for <b>{level} → {group}</b>.\n\n"
        "You can send:\n"
        "• plain text\n"
        "• PDF, Word, or any document\n"
        "• photo (with optional caption)\n"
        "• video, audio, or voice message\n\n"
        "Send /cancel to abort."
    )
    await callback.answer()


@router.message(StateFilter(AddContent.waiting_for_content))
async def admin_receive_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    level = data.get("level")
    group = data.get("group")
    section = data.get("section")

    file_id = None
    file_type = None
    text = None
    caption = message.caption

    if message.photo:
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
        await message.answer("⚠️ Unsupported type. Send text, photo, video, audio, or document.")
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
    await message.answer(
        f"✅ Saved!\n\n"
        f"<b>ID:</b> {new_id}\n"
        f"<b>Level:</b> {level}\n"
        f"<b>Group:</b> {group}\n"
        f"<b>Section:</b> {section}\n"
        f"<b>Type:</b> {file_type or 'text'}"
    )


# ---------- /show_content ----------

@router.message(Command("show_content"))
async def cmd_show_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(ShowContent.waiting_for_level)
    await message.answer(
        "🔎 Choose a <b>level</b>:",
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
    _, _, _, level, group, section = parts
    await state.clear()
    rows = get_content(level, group, section)
    if not rows:
        await callback.message.edit_text(
            f"📭 No content for <b>{level} → {group} → {section}</b>."
        )
        await callback.answer()
        return
    lines = [f"📋 <b>{level} → {group} → {section}</b>\n"]
    for row in rows:
        kind = row["file_type"] or "text"
        preview = (row["text"] or row["caption"] or "")[:60].replace("\n", " ")
        lines.append(f"• <b>ID {row['id']}</b> [{kind}] {preview}")
    lines.append("\nUse /delete_content to remove an item.")
    await callback.message.edit_text("\n".join(lines))
    await callback.answer()


# ---------- /delete_content ----------

@router.message(Command("delete_content"))
async def cmd_delete_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(DeleteContent.waiting_for_id)
    await message.answer(
        "🗑 Send the <b>ID</b> of the content to delete.\n"
        "Use /show_content first to find IDs.\n\n"
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
        await message.answer("⛔ Admins only.")
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
            failed += 1
    await message.answer(f"✅ Sent to {sent} students. Failed: {failed}.")


# ---------- CANCEL BUTTON ----------

@router.callback_query(F.data == "adm|cancel")
async def admin_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("✅ Cancelled.")
    await callback.answer()


# ---------- NOOP (empty group button) ----------

@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer("No groups available.", show_alert=True)
