"""
Admin handlers — groups AND sections are fully dynamic.

Group commands:   /add_group  /delete_group  /rename_group  /list_groups
Section commands: /add_section /delete_section /rename_section /list_sections
Content commands: /add_homework /add_task /add_material /add_book
                  /add_recorded_lesson /add_lesson_file
                  /show_content /delete_content
Other:            /announcement /cancel
"""

import os
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import (
    LEVELS,
    add_content, get_content, get_content_by_id, delete_content,
    add_group, delete_group, rename_group, get_groups, get_all_groups,
    add_section, delete_section, rename_section, get_sections, get_all_sections,
    add_announcement, get_all_user_ids,
)
from keyboards import (
    admin_levels_keyboard,
    admin_groups_keyboard,
    admin_sections_keyboard,
    admin_sections_manage_keyboard,
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


# ══════════════════════════ FSM STATES ══════════════════════════

class AddContent(StatesGroup):
    waiting_for_level = State()
    waiting_for_group = State()
    waiting_for_section = State()
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


class AddSection(StatesGroup):
    waiting_for_level = State()
    waiting_for_name = State()


class DeleteSection(StatesGroup):
    waiting_for_level = State()
    waiting_for_section = State()


class RenameSection(StatesGroup):
    waiting_for_level = State()
    waiting_for_section = State()
    waiting_for_new_name = State()


# ══════════════════════════ /cancel ══════════════════════════

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if await state.get_state() is None:
        await message.answer("Nothing to cancel.")
        return
    await state.clear()
    await message.answer("✅ Cancelled.")


# ══════════════════════════ GROUP COMMANDS ══════════════════════════

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
    lines = ["📋 <b>All groups:</b>"]
    for row in rows:
        if row["level"] != current_level:
            current_level = row["level"]
            lines.append(f"\n<b>{current_level}</b>")
        lines.append(f"  • {row['group_name']}")
    await message.answer("\n".join(lines))


@router.message(Command("add_group"))
async def cmd_add_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(AddGroup.waiting_for_level)
    await message.answer(
        "➕ <b>Add a new group</b>\n\nChoose the <b>level</b>:",
        reply_markup=admin_levels_keyboard("addgrp"),
    )


@router.callback_query(StateFilter(AddGroup.waiting_for_level), F.data.startswith("adm|addgrp|lvl|"))
async def add_group_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(AddGroup.waiting_for_name)
    existing = get_groups(level)
    existing_text = ", ".join(existing) if existing else "none yet"
    await callback.message.edit_text(
        f"➕ Adding group to <b>{level}</b>\n\n"
        f"Current groups: <i>{existing_text}</i>\n\n"
        f"Type the <b>new group name</b> and send it:"
    )
    await callback.answer()


@router.message(StateFilter(AddGroup.waiting_for_name))
async def add_group_receive_name(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Please send a name, or /cancel.")
        return
    data = await state.get_data()
    level = data.get("level")
    success = add_group(level, name)
    await state.clear()
    if success:
        await message.answer(f"✅ Group <b>{name}</b> added to <b>{level}</b>!")
    else:
        await message.answer(f"⚠️ Group <b>{name}</b> already exists in <b>{level}</b>.")


@router.message(Command("delete_group"))
async def cmd_delete_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(DeleteGroup.waiting_for_level)
    await message.answer(
        "🗑 <b>Delete a group</b>\n\n"
        "⚠️ This also deletes ALL content in that group.\n\n"
        "Choose the <b>level</b>:",
        reply_markup=admin_levels_keyboard("delgrp"),
    )


@router.callback_query(StateFilter(DeleteGroup.waiting_for_level), F.data.startswith("adm|delgrp|lvl|"))
async def delete_group_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(DeleteGroup.waiting_for_group)
    await callback.message.edit_text(
        f"🗑 <b>{level}</b>\n\nChoose the <b>group to delete</b>:",
        reply_markup=admin_groups_keyboard("delgrp", level),
    )
    await callback.answer()


@router.callback_query(StateFilter(DeleteGroup.waiting_for_group), F.data.startswith("adm|delgrp|grp|"))
async def delete_group_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.clear()
    success = delete_group(level, group)
    if success:
        await callback.message.edit_text(
            f"✅ Group <b>{group}</b> deleted from <b>{level}</b>.\n"
            f"All its content was also removed."
        )
    else:
        await callback.message.edit_text(f"❌ Could not find group <b>{group}</b> in <b>{level}</b>.")
    await callback.answer()


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


@router.callback_query(StateFilter(RenameGroup.waiting_for_level), F.data.startswith("adm|rengrp|lvl|"))
async def rename_group_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(RenameGroup.waiting_for_group)
    await callback.message.edit_text(
        f"✏️ <b>{level}</b>\n\nChoose the <b>group to rename</b>:",
        reply_markup=admin_groups_keyboard("rengrp", level),
    )
    await callback.answer()


@router.callback_query(StateFilter(RenameGroup.waiting_for_group), F.data.startswith("adm|rengrp|grp|"))
async def rename_group_pick_group(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.update_data(level=level, old_name=group)
    await state.set_state(RenameGroup.waiting_for_new_name)
    await callback.message.edit_text(
        f"✏️ Renaming <b>{group}</b> in <b>{level}</b>\n\nSend the <b>new name</b>:"
    )
    await callback.answer()


@router.message(StateFilter(RenameGroup.waiting_for_new_name))
async def rename_group_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("⚠️ Please send a name, or /cancel.")
        return
    data = await state.get_data()
    success = rename_group(data["level"], data["old_name"], new_name)
    await state.clear()
    if success:
        await message.answer(
            f"✅ Renamed <b>{data['old_name']}</b> → <b>{new_name}</b> in <b>{data['level']}</b>.\n"
            f"All content moved automatically."
        )
    else:
        await message.answer(f"❌ Could not rename. Name may already exist.")


# ══════════════════════════ SECTION COMMANDS ══════════════════════════

@router.message(Command("list_sections"))
async def cmd_list_sections(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    rows = get_all_sections()
    if not rows:
        await message.answer("No sections found.")
        return
    current_level = None
    lines = ["📋 <b>All sections per level:</b>"]
    for row in rows:
        if row["level"] != current_level:
            current_level = row["level"]
            lines.append(f"\n<b>{current_level}</b>")
        lines.append(f"  • {row['section_name']}")
    await message.answer("\n".join(lines))


@router.message(Command("add_section"))
async def cmd_add_section(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(AddSection.waiting_for_level)
    await message.answer(
        "➕ <b>Add a new section</b>\n\nChoose the <b>level</b> to add a section to:",
        reply_markup=admin_levels_keyboard("addsec"),
    )


@router.callback_query(StateFilter(AddSection.waiting_for_level), F.data.startswith("adm|addsec|lvl|"))
async def add_section_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(AddSection.waiting_for_name)
    existing = get_sections(level)
    existing_text = ", ".join(existing) if existing else "none yet"
    await callback.message.edit_text(
        f"➕ Adding section to <b>{level}</b>\n\n"
        f"Current sections: <i>{existing_text}</i>\n\n"
        f"Type the <b>new section name</b> and send it:\n\n"
        f"Examples:\n"
        f"• Mock Tests\n"
        f"• Speaking Tasks\n"
        f"• Writing Feedback\n"
        f"• Vocabulary\n"
        f"• Listening"
    )
    await callback.answer()


@router.message(StateFilter(AddSection.waiting_for_name))
async def add_section_receive_name(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Please send a section name, or /cancel.")
        return
    data = await state.get_data()
    level = data.get("level")
    success = add_section(level, name)
    await state.clear()
    if success:
        await message.answer(
            f"✅ Section <b>{name}</b> added to <b>{level}</b>!\n\n"
            f"Students in {level} will now see this section."
        )
    else:
        await message.answer(f"⚠️ Section <b>{name}</b> already exists in <b>{level}</b>.")


@router.message(Command("delete_section"))
async def cmd_delete_section(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(DeleteSection.waiting_for_level)
    await message.answer(
        "🗑 <b>Delete a section</b>\n\n"
        "⚠️ This also deletes ALL content in that section for this level.\n\n"
        "Choose the <b>level</b>:",
        reply_markup=admin_levels_keyboard("delsec"),
    )


@router.callback_query(StateFilter(DeleteSection.waiting_for_level), F.data.startswith("adm|delsec|lvl|"))
async def delete_section_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(DeleteSection.waiting_for_section)
    await callback.message.edit_text(
        f"🗑 <b>{level}</b>\n\nChoose the <b>section to delete</b>:",
        reply_markup=admin_sections_manage_keyboard("delsec", level),
    )
    await callback.answer()


@router.callback_query(StateFilter(DeleteSection.waiting_for_section), F.data.startswith("adm|delsec|msec|"))
async def delete_section_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, section = callback.data.split("|", 4)
    await state.clear()
    success = delete_section(level, section)
    if success:
        await callback.message.edit_text(
            f"✅ Section <b>{section}</b> deleted from <b>{level}</b>.\n"
            f"All its content was also removed."
        )
    else:
        await callback.message.edit_text(f"❌ Could not find section <b>{section}</b> in <b>{level}</b>.")
    await callback.answer()


@router.message(Command("rename_section"))
async def cmd_rename_section(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(RenameSection.waiting_for_level)
    await message.answer(
        "✏️ <b>Rename a section</b>\n\nChoose the <b>level</b>:",
        reply_markup=admin_levels_keyboard("rensec"),
    )


@router.callback_query(StateFilter(RenameSection.waiting_for_level), F.data.startswith("adm|rensec|lvl|"))
async def rename_section_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(RenameSection.waiting_for_section)
    await callback.message.edit_text(
        f"✏️ <b>{level}</b>\n\nChoose the <b>section to rename</b>:",
        reply_markup=admin_sections_manage_keyboard("rensec", level),
    )
    await callback.answer()


@router.callback_query(StateFilter(RenameSection.waiting_for_section), F.data.startswith("adm|rensec|msec|"))
async def rename_section_pick_section(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, section = callback.data.split("|", 4)
    await state.update_data(level=level, old_name=section)
    await state.set_state(RenameSection.waiting_for_new_name)
    await callback.message.edit_text(
        f"✏️ Renaming <b>{section}</b> in <b>{level}</b>\n\nSend the <b>new name</b>:"
    )
    await callback.answer()


@router.message(StateFilter(RenameSection.waiting_for_new_name))
async def rename_section_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("⚠️ Please send a name, or /cancel.")
        return
    data = await state.get_data()
    success = rename_section(data["level"], data["old_name"], new_name)
    await state.clear()
    if success:
        await message.answer(
            f"✅ Renamed <b>{data['old_name']}</b> → <b>{new_name}</b> in <b>{data['level']}</b>.\n"
            f"All content moved automatically."
        )
    else:
        await message.answer(f"❌ Could not rename. Name may already exist.")


# ══════════════════════════ ADD CONTENT COMMANDS ══════════════════════════

@router.message(Command(commands=list(SECTION_BY_COMMAND.keys())))
async def cmd_add_content_shortcut(message: Message, state: FSMContext) -> None:
    """Shortcut commands like /add_homework — skip section selection."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    command = message.text.split()[0].lstrip("/").split("@")[0]
    section = SECTION_BY_COMMAND.get(command)
    if not section:
        return
    await state.clear()
    await state.update_data(section=section)
    await state.set_state(AddContent.waiting_for_level)
    await message.answer(
        f"📌 Adding <b>{section}</b>.\n\nChoose a <b>level</b>:",
        reply_markup=admin_levels_keyboard("add"),
    )


@router.message(Command("add_content"))
async def cmd_add_content(message: Message, state: FSMContext) -> None:
    """Generic add content — lets admin pick the section too."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.update_data(section=None)
    await state.set_state(AddContent.waiting_for_level)
    await message.answer(
        "📌 <b>Add content</b>\n\nChoose a <b>level</b>:",
        reply_markup=admin_levels_keyboard("add"),
    )


@router.callback_query(StateFilter(AddContent.waiting_for_level), F.data.startswith("adm|add|lvl|"))
async def add_content_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(AddContent.waiting_for_group)
    await callback.message.edit_text(
        f"📂 Level: <b>{level}</b>\n\nChoose a <b>group</b>:",
        reply_markup=admin_groups_keyboard("add", level),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddContent.waiting_for_group), F.data.startswith("adm|add|grp|"))
async def add_content_pick_group(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.update_data(group=group)
    data = await state.get_data()
    section = data.get("section")

    if section:
        # Shortcut command already set the section — skip selection
        await state.set_state(AddContent.waiting_for_content)
        await callback.message.edit_text(
            f"📥 Send the <b>{section}</b> for <b>{level} → {group}</b>.\n\n"
            "You can send: text, PDF, Word, photo, video, audio, voice.\n\n"
            "Send /cancel to abort."
        )
    else:
        # Generic add_content — ask which section
        await state.set_state(AddContent.waiting_for_section)
        await callback.message.edit_text(
            f"📁 <b>{level} → {group}</b>\n\nChoose a <b>section</b>:",
            reply_markup=admin_sections_keyboard("add", level, group),
        )
    await callback.answer()


@router.callback_query(StateFilter(AddContent.waiting_for_section), F.data.startswith("adm|add|sec|"))
async def add_content_pick_section(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, level, group, section = parts
    await state.update_data(section=section)
    await state.set_state(AddContent.waiting_for_content)
    await callback.message.edit_text(
        f"📥 Send the <b>{section}</b> for <b>{level} → {group}</b>.\n\n"
        "You can send: text, PDF, Word, photo, video, audio, voice.\n\n"
        "Send /cancel to abort."
    )
    await callback.answer()


@router.message(StateFilter(AddContent.waiting_for_content))
async def add_content_receive(message: Message, state: FSMContext) -> None:
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
        level=level, group_name=group, section=section,
        text=text, file_id=file_id, file_type=file_type, caption=caption,
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


# ══════════════════════════ SHOW / DELETE CONTENT ══════════════════════════

@router.message(Command("show_content"))
async def cmd_show_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(ShowContent.waiting_for_level)
    await message.answer("🔎 Choose a <b>level</b>:", reply_markup=admin_levels_keyboard("show"))


@router.callback_query(StateFilter(ShowContent.waiting_for_level), F.data.startswith("adm|show|lvl|"))
async def show_content_pick_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.split("|", 3)[3]
    await state.update_data(level=level)
    await state.set_state(ShowContent.waiting_for_group)
    await callback.message.edit_text(
        f"📂 <b>{level}</b>\n\nChoose a <b>group</b>:",
        reply_markup=admin_groups_keyboard("show", level),
    )
    await callback.answer()


@router.callback_query(StateFilter(ShowContent.waiting_for_group), F.data.startswith("adm|show|grp|"))
async def show_content_pick_group(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, _, level, group = callback.data.split("|", 4)
    await state.update_data(group=group)
    await state.set_state(ShowContent.waiting_for_section)
    await callback.message.edit_text(
        f"📁 <b>{level} → {group}</b>\n\nChoose a <b>section</b>:",
        reply_markup=admin_sections_keyboard("show", level, group),
    )
    await callback.answer()


@router.callback_query(StateFilter(ShowContent.waiting_for_section), F.data.startswith("adm|show|sec|"))
async def show_content_pick_section(callback: CallbackQuery, state: FSMContext) -> None:
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
async def delete_content_by_id(message: Message, state: FSMContext) -> None:
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


# ══════════════════════════ ANNOUNCEMENT ══════════════════════════

@router.message(Command("announcement"))
async def cmd_announcement(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(Announcement.waiting_for_text)
    await message.answer("📣 Send the announcement text to broadcast to all students.\nSend /cancel to abort.")


@router.message(StateFilter(Announcement.waiting_for_text))
async def send_announcement(message: Message, state: FSMContext) -> None:
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
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, f"📣 <b>Announcement</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Sent to {sent} students. Failed: {failed}.")


# ══════════════════════════ UTILITY ══════════════════════════

@router.callback_query(F.data == "adm|cancel")
async def admin_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("✅ Cancelled.")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer("Nothing here yet.", show_alert=True)
