"""
Admin handlers — full control over every part of the bot structure.

Commands grouped by what they manage:

CATEGORIES   /add_category /delete_category /rename_category /list_categories
DAY TYPES    /add_day_type /delete_day_type /rename_day_type /list_day_types
TIME SLOTS   /add_time_slot /delete_time_slot /rename_time_slot /list_time_slots
GROUP NAMES  /add_group /delete_group /rename_group /list_groups
SECTIONS     /add_section /delete_section /rename_section /list_sections
CONTENT      /add_content /show_content /delete_content
OTHER        /announcement /cancel
"""

import os
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import (
    get_categories, add_category, delete_category, rename_category,
    get_day_types, add_day_type, delete_day_type, rename_day_type,
    get_time_slots, get_all_time_slots, add_time_slot, delete_time_slot, rename_time_slot,
    get_group_names, add_group_name, delete_group_name, rename_group_name,
    get_sections, get_all_sections, add_section, delete_section, rename_section,
    add_content, get_content, get_content_by_id, delete_content_by_id,
    add_announcement, get_all_user_ids,
)
from keyboards import (
    adm_categories_keyboard, adm_day_types_keyboard, adm_time_slots_keyboard,
    adm_group_names_keyboard, adm_sections_keyboard, adm_sections_manage_keyboard,
    adm_manage_list_keyboard,
)

router = Router(name="admin")

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


# ══════════════ FSM STATES ══════════════

class AddContent(StatesGroup):
    pick_category = State()
    pick_day_type = State()
    pick_time_slot = State()
    pick_group = State()
    pick_section = State()
    receive_content = State()


class ShowContent(StatesGroup):
    pick_category = State()
    pick_day_type = State()
    pick_time_slot = State()
    pick_group = State()
    pick_section = State()


class DeleteContent(StatesGroup):
    waiting_id = State()


class Announcement(StatesGroup):
    waiting_text = State()


# Generic 2-step: pick item from list → receive new name
class SimpleAdd(StatesGroup):
    waiting_name = State()


class SimplePick(StatesGroup):
    picked = State()


class SimpleRename(StatesGroup):
    pick_item = State()
    new_name = State()


class TimeSlotAdd(StatesGroup):
    pick_day_type = State()
    waiting_slot = State()


class TimeSlotDelete(StatesGroup):
    pick_day_type = State()
    pick_slot = State()


class TimeSlotRename(StatesGroup):
    pick_day_type = State()
    pick_slot = State()
    new_name = State()


class SectionAdd(StatesGroup):
    pick_category = State()
    waiting_name = State()


class SectionDelete(StatesGroup):
    pick_category = State()
    pick_section = State()


class SectionRename(StatesGroup):
    pick_category = State()
    pick_section = State()
    new_name = State()


# ══════════════ /cancel ══════════════

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if await state.get_state() is None:
        await message.answer("Nothing to cancel.")
        return
    await state.clear()
    await message.answer("✅ Cancelled.")


@router.callback_query(F.data == "adm|cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("✅ Cancelled.")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer("Nothing here yet.", show_alert=True)


# ══════════════ CATEGORIES ══════════════

@router.message(Command("list_categories"))
async def cmd_list_categories(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    cats = get_categories()
    lines = ["📋 <b>Main menu categories:</b>\n"] + [f"  {i+1}. {c}" for i, c in enumerate(cats)]
    await message.answer("\n".join(lines))


@router.message(Command("add_category"))
async def cmd_add_category(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="category")
    await state.set_state(SimpleAdd.waiting_name)
    existing = ", ".join(get_categories())
    await message.answer(
        f"➕ <b>Add category</b>\n\nExisting: <i>{existing}</i>\n\nSend the new category name:"
    )


@router.message(Command("delete_category"))
async def cmd_delete_category(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="category")
    await state.set_state(SimplePick.picked)
    await message.answer(
        "🗑 <b>Delete category</b>\n⚠️ All sections and content in it will be deleted.\n\nChoose:",
        reply_markup=adm_manage_list_keyboard("delcat", get_categories(), "item"),
    )


@router.message(Command("rename_category"))
async def cmd_rename_category(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(SimpleRename.pick_item)
    await state.update_data(mode="category")
    await message.answer(
        "✏️ <b>Rename category</b>\n\nChoose the category to rename:",
        reply_markup=adm_manage_list_keyboard("rencat", get_categories(), "item"),
    )


@router.callback_query(StateFilter(SimplePick.picked), F.data.startswith("adm|delcat|item|"))
async def cb_delete_category(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("|", 3)[3]
    await state.clear()
    success = delete_category(name)
    await callback.message.edit_text(
        f"✅ Category <b>{name}</b> deleted." if success else f"❌ Could not delete <b>{name}</b>."
    )
    await callback.answer()


@router.callback_query(StateFilter(SimpleRename.pick_item), F.data.startswith("adm|rencat|item|"))
async def cb_rename_category_pick(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("|", 3)[3]
    await state.update_data(old_name=name)
    await state.set_state(SimpleRename.new_name)
    await callback.message.edit_text(f"✏️ Renaming <b>{name}</b>. Send the new name:")
    await callback.answer()


# ══════════════ DAY TYPES ══════════════

@router.message(Command("list_day_types"))
async def cmd_list_day_types(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    items = get_day_types()
    lines = ["📅 <b>Day types:</b>\n"] + [f"  • {d}" for d in items]
    await message.answer("\n".join(lines))


@router.message(Command("add_day_type"))
async def cmd_add_day_type(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="day_type")
    await state.set_state(SimpleAdd.waiting_name)
    await message.answer(
        f"➕ <b>Add day type</b>\n\nExisting: <i>{', '.join(get_day_types())}</i>\n\nSend the name:\n(e.g. Weekend, Monday Only)"
    )


@router.message(Command("delete_day_type"))
async def cmd_delete_day_type(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="day_type")
    await state.set_state(SimplePick.picked)
    await message.answer(
        "🗑 <b>Delete day type</b>\n⚠️ All time slots and content in it will be deleted.\n\nChoose:",
        reply_markup=adm_manage_list_keyboard("deldt", get_day_types(), "item"),
    )


@router.message(Command("rename_day_type"))
async def cmd_rename_day_type(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="day_type")
    await state.set_state(SimpleRename.pick_item)
    await message.answer(
        "✏️ <b>Rename day type</b>\n\nChoose:",
        reply_markup=adm_manage_list_keyboard("rendt", get_day_types(), "item"),
    )


@router.callback_query(StateFilter(SimplePick.picked), F.data.startswith("adm|deldt|item|"))
async def cb_delete_day_type(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("|", 3)[3]
    await state.clear()
    success = delete_day_type(name)
    await callback.message.edit_text(
        f"✅ Day type <b>{name}</b> deleted." if success else f"❌ Not found."
    )
    await callback.answer()


@router.callback_query(StateFilter(SimpleRename.pick_item), F.data.startswith("adm|rendt|item|"))
async def cb_rename_day_type_pick(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("|", 3)[3]
    await state.update_data(old_name=name, mode="day_type")
    await state.set_state(SimpleRename.new_name)
    await callback.message.edit_text(f"✏️ Renaming <b>{name}</b>. Send the new name:")
    await callback.answer()


# ══════════════ TIME SLOTS ══════════════

@router.message(Command("list_time_slots"))
async def cmd_list_time_slots(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    rows = get_all_time_slots()
    if not rows:
        await message.answer("No time slots found.")
        return
    current_dt = None
    lines = ["🕐 <b>Time slots:</b>"]
    for row in rows:
        if row["day_type"] != current_dt:
            current_dt = row["day_type"]
            lines.append(f"\n<b>{current_dt}</b>")
        lines.append(f"  • {row['slot']}")
    await message.answer("\n".join(lines))


@router.message(Command("add_time_slot"))
async def cmd_add_time_slot(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(TimeSlotAdd.pick_day_type)
    await message.answer(
        "➕ <b>Add time slot</b>\n\nChoose the day type:",
        reply_markup=adm_manage_list_keyboard("tsadd", get_day_types(), "dt"),
    )


@router.callback_query(StateFilter(TimeSlotAdd.pick_day_type), F.data.startswith("adm|tsadd|dt|"))
async def ts_add_pick_dt(callback: CallbackQuery, state: FSMContext) -> None:
    day_type = callback.data.split("|", 3)[3]
    await state.update_data(day_type=day_type)
    await state.set_state(TimeSlotAdd.waiting_slot)
    existing = ", ".join(get_time_slots(day_type)) or "none"
    await callback.message.edit_text(
        f"➕ Adding slot to <b>{day_type}</b>\n\nExisting: <i>{existing}</i>\n\n"
        f"Send the new time slot:\n(e.g. 11:30-13:30)"
    )
    await callback.answer()


@router.message(StateFilter(TimeSlotAdd.waiting_slot))
async def ts_add_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    slot = (message.text or "").strip()
    if not slot:
        await message.answer("⚠️ Please send a time slot, or /cancel.")
        return
    data = await state.get_data()
    success = add_time_slot(data["day_type"], slot)
    await state.clear()
    if success:
        await message.answer(f"✅ Time slot <b>{slot}</b> added to <b>{data['day_type']}</b>!")
    else:
        await message.answer(f"⚠️ <b>{slot}</b> already exists in <b>{data['day_type']}</b>.")


@router.message(Command("delete_time_slot"))
async def cmd_delete_time_slot(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(TimeSlotDelete.pick_day_type)
    await message.answer(
        "🗑 <b>Delete time slot</b>\n\nChoose the day type:",
        reply_markup=adm_manage_list_keyboard("tsdel", get_day_types(), "dt"),
    )


@router.callback_query(StateFilter(TimeSlotDelete.pick_day_type), F.data.startswith("adm|tsdel|dt|"))
async def ts_del_pick_dt(callback: CallbackQuery, state: FSMContext) -> None:
    day_type = callback.data.split("|", 3)[3]
    await state.update_data(day_type=day_type)
    await state.set_state(TimeSlotDelete.pick_slot)
    await callback.message.edit_text(
        f"🗑 <b>{day_type}</b> — choose the slot to delete:",
        reply_markup=adm_manage_list_keyboard("tsdel2", get_time_slots(day_type), "sl"),
    )
    await callback.answer()


@router.callback_query(StateFilter(TimeSlotDelete.pick_slot), F.data.startswith("adm|tsdel2|sl|"))
async def ts_del_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    slot = callback.data.split("|", 3)[3]
    data = await state.get_data()
    await state.clear()
    success = delete_time_slot(data["day_type"], slot)
    await callback.message.edit_text(
        f"✅ Slot <b>{slot}</b> deleted from <b>{data['day_type']}</b>." if success else "❌ Not found."
    )
    await callback.answer()


@router.message(Command("rename_time_slot"))
async def cmd_rename_time_slot(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(TimeSlotRename.pick_day_type)
    await message.answer(
        "✏️ <b>Rename time slot</b>\n\nChoose the day type:",
        reply_markup=adm_manage_list_keyboard("tsren", get_day_types(), "dt"),
    )


@router.callback_query(StateFilter(TimeSlotRename.pick_day_type), F.data.startswith("adm|tsren|dt|"))
async def ts_ren_pick_dt(callback: CallbackQuery, state: FSMContext) -> None:
    day_type = callback.data.split("|", 3)[3]
    await state.update_data(day_type=day_type)
    await state.set_state(TimeSlotRename.pick_slot)
    await callback.message.edit_text(
        f"✏️ <b>{day_type}</b> — choose slot to rename:",
        reply_markup=adm_manage_list_keyboard("tsren2", get_time_slots(day_type), "sl"),
    )
    await callback.answer()


@router.callback_query(StateFilter(TimeSlotRename.pick_slot), F.data.startswith("adm|tsren2|sl|"))
async def ts_ren_pick_slot(callback: CallbackQuery, state: FSMContext) -> None:
    slot = callback.data.split("|", 3)[3]
    await state.update_data(old_name=slot)
    await state.set_state(TimeSlotRename.new_name)
    await callback.message.edit_text(f"✏️ Renaming <b>{slot}</b>. Send the new time slot:")
    await callback.answer()


@router.message(StateFilter(TimeSlotRename.new_name))
async def ts_ren_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("⚠️ Send a time slot or /cancel.")
        return
    data = await state.get_data()
    success = rename_time_slot(data["day_type"], data["old_name"], new_name)
    await state.clear()
    if success:
        await message.answer(f"✅ Renamed <b>{data['old_name']}</b> → <b>{new_name}</b>.")
    else:
        await message.answer("❌ Could not rename.")


# ══════════════ GROUP NAMES ══════════════

@router.message(Command("list_groups"))
async def cmd_list_groups(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    items = get_group_names()
    lines = ["🏷 <b>Group names:</b>\n"] + [f"  • {g}" for g in items]
    await message.answer("\n".join(lines))


@router.message(Command("add_group"))
async def cmd_add_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="group")
    await state.set_state(SimpleAdd.waiting_name)
    await message.answer(
        f"➕ <b>Add group name</b>\n\nExisting: <i>{', '.join(get_group_names())}</i>\n\n"
        f"Send the new group name:\n(e.g. Warriors, Champions)"
    )


@router.message(Command("delete_group"))
async def cmd_delete_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="group")
    await state.set_state(SimplePick.picked)
    await message.answer(
        "🗑 <b>Delete group name</b>\n\nChoose:",
        reply_markup=adm_manage_list_keyboard("delgn", get_group_names(), "item"),
    )


@router.message(Command("rename_group"))
async def cmd_rename_group(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.update_data(mode="group")
    await state.set_state(SimpleRename.pick_item)
    await message.answer(
        "✏️ <b>Rename group name</b>\n\nChoose:",
        reply_markup=adm_manage_list_keyboard("rengn", get_group_names(), "item"),
    )


@router.callback_query(StateFilter(SimplePick.picked), F.data.startswith("adm|delgn|item|"))
async def cb_delete_group(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("|", 3)[3]
    await state.clear()
    success = delete_group_name(name)
    await callback.message.edit_text(
        f"✅ Group <b>{name}</b> deleted." if success else "❌ Not found."
    )
    await callback.answer()


@router.callback_query(StateFilter(SimpleRename.pick_item), F.data.startswith("adm|rengn|item|"))
async def cb_rename_group_pick(callback: CallbackQuery, state: FSMContext) -> None:
    name = callback.data.split("|", 3)[3]
    await state.update_data(old_name=name, mode="group")
    await state.set_state(SimpleRename.new_name)
    await callback.message.edit_text(f"✏️ Renaming <b>{name}</b>. Send the new name:")
    await callback.answer()


# ══════════════ SECTIONS ══════════════

@router.message(Command("list_sections"))
async def cmd_list_sections(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    rows = get_all_sections()
    if not rows:
        await message.answer("No sections found.")
        return
    current_cat = None
    lines = ["📋 <b>Sections per category:</b>"]
    for row in rows:
        if row["category"] != current_cat:
            current_cat = row["category"]
            lines.append(f"\n<b>{current_cat}</b>")
        lines.append(f"  • {row['name']}")
    await message.answer("\n".join(lines))


@router.message(Command("add_section"))
async def cmd_add_section(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(SectionAdd.pick_category)
    await message.answer(
        "➕ <b>Add section</b>\n\nChoose the category:",
        reply_markup=adm_categories_keyboard("addsec"),
    )


@router.callback_query(StateFilter(SectionAdd.pick_category), F.data.startswith("adm|addsec|cat|"))
async def sec_add_pick_cat(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split("|", 3)[3]
    await state.update_data(category=category)
    await state.set_state(SectionAdd.waiting_name)
    existing = ", ".join(get_sections(category)) or "none"
    await callback.message.edit_text(
        f"➕ Adding section to <b>{category}</b>\n\nExisting: <i>{existing}</i>\n\n"
        f"Send the new section name:\n(e.g. Mock Tests, Vocabulary, Speaking Tasks)"
    )
    await callback.answer()


@router.message(StateFilter(SectionAdd.waiting_name))
async def sec_add_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Send a name or /cancel.")
        return
    data = await state.get_data()
    success = add_section(data["category"], name)
    await state.clear()
    if success:
        await message.answer(f"✅ Section <b>{name}</b> added to <b>{data['category']}</b>!")
    else:
        await message.answer(f"⚠️ Already exists.")


@router.message(Command("delete_section"))
async def cmd_delete_section(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(SectionDelete.pick_category)
    await message.answer(
        "🗑 <b>Delete section</b>\n\nChoose the category:",
        reply_markup=adm_categories_keyboard("delsec"),
    )


@router.callback_query(StateFilter(SectionDelete.pick_category), F.data.startswith("adm|delsec|cat|"))
async def sec_del_pick_cat(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split("|", 3)[3]
    await state.update_data(category=category)
    await state.set_state(SectionDelete.pick_section)
    await callback.message.edit_text(
        f"🗑 <b>{category}</b>\n\nChoose section to delete:",
        reply_markup=adm_sections_manage_keyboard("delsec2", category),
    )
    await callback.answer()


@router.callback_query(StateFilter(SectionDelete.pick_section), F.data.startswith("adm|delsec2|msec|"))
async def sec_del_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|", 4)
    _, _, _, category, section = parts
    await state.clear()
    success = delete_section(category, section)
    await callback.message.edit_text(
        f"✅ Section <b>{section}</b> deleted from <b>{category}</b>." if success else "❌ Not found."
    )
    await callback.answer()


@router.message(Command("rename_section"))
async def cmd_rename_section(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(SectionRename.pick_category)
    await message.answer(
        "✏️ <b>Rename section</b>\n\nChoose the category:",
        reply_markup=adm_categories_keyboard("rensec"),
    )


@router.callback_query(StateFilter(SectionRename.pick_category), F.data.startswith("adm|rensec|cat|"))
async def sec_ren_pick_cat(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split("|", 3)[3]
    await state.update_data(category=category)
    await state.set_state(SectionRename.pick_section)
    await callback.message.edit_text(
        f"✏️ <b>{category}</b>\n\nChoose section to rename:",
        reply_markup=adm_sections_manage_keyboard("rensec2", category),
    )
    await callback.answer()


@router.callback_query(StateFilter(SectionRename.pick_section), F.data.startswith("adm|rensec2|msec|"))
async def sec_ren_pick_sec(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|", 4)
    _, _, _, category, section = parts
    await state.update_data(category=category, old_name=section)
    await state.set_state(SectionRename.new_name)
    await callback.message.edit_text(f"✏️ Renaming <b>{section}</b>. Send the new name:")
    await callback.answer()


@router.message(StateFilter(SectionRename.new_name))
async def sec_ren_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("⚠️ Send a name or /cancel.")
        return
    data = await state.get_data()
    success = rename_section(data["category"], data["old_name"], new_name)
    await state.clear()
    if success:
        await message.answer(f"✅ Renamed <b>{data['old_name']}</b> → <b>{new_name}</b>.")
    else:
        await message.answer("❌ Could not rename.")


# ══════════════ SHARED FSM RECEIVERS ══════════════

@router.message(StateFilter(SimpleAdd.waiting_name))
async def simple_add_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Send a name or /cancel.")
        return
    data = await state.get_data()
    mode = data.get("mode")
    if mode == "category":
        success = add_category(name)
    elif mode == "day_type":
        success = add_day_type(name)
    elif mode == "group":
        success = add_group_name(name)
    else:
        success = False
    await state.clear()
    await message.answer(f"✅ <b>{name}</b> added!" if success else f"⚠️ <b>{name}</b> already exists.")


@router.message(StateFilter(SimpleRename.new_name))
async def simple_rename_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("⚠️ Send a name or /cancel.")
        return
    data = await state.get_data()
    mode = data.get("mode")
    old = data.get("old_name")
    if mode == "category":
        success = rename_category(old, new_name)
    elif mode == "day_type":
        success = rename_day_type(old, new_name)
    elif mode == "group":
        success = rename_group_name(old, new_name)
    else:
        success = False
    await state.clear()
    if success:
        await message.answer(f"✅ Renamed <b>{old}</b> → <b>{new_name}</b>.")
    else:
        await message.answer("❌ Could not rename.")


# ══════════════ ADD CONTENT ══════════════

@router.message(Command("add_content"))
async def cmd_add_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(AddContent.pick_category)
    await message.answer(
        "📌 <b>Add content</b>\n\nChoose a category:",
        reply_markup=adm_categories_keyboard("addcon"),
    )


@router.callback_query(StateFilter(AddContent.pick_category), F.data.startswith("adm|addcon|cat|"))
async def add_con_pick_cat(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split("|", 3)[3]
    await state.update_data(category=category, day_type="", time_slot="", group_name="")
    if category == GROUPS_CATEGORY:
        await state.set_state(AddContent.pick_day_type)
        await callback.message.edit_text(
            f"📌 <b>{category}</b>\n\nChoose day type:",
            reply_markup=adm_day_types_keyboard("addcon", category),
        )
    elif category == UNIVERSAL_CATEGORY:
        await state.set_state(AddContent.pick_group)
        await callback.message.edit_text(
            f"📌 <b>{category}</b>\n\nChoose group:",
            reply_markup=adm_group_names_keyboard("addcon", category),
        )
    else:
        await state.set_state(AddContent.pick_section)
        await callback.message.edit_text(
            f"📌 <b>{category}</b>\n\nChoose section:",
            reply_markup=adm_sections_keyboard("addcon", category),
        )
    await callback.answer()


@router.callback_query(StateFilter(AddContent.pick_day_type), F.data.startswith("adm|addcon|dt|"))
async def add_con_pick_dt(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type = parts
    await state.update_data(day_type=day_type)
    await state.set_state(AddContent.pick_time_slot)
    data = await state.get_data()
    await callback.message.edit_text(
        f"📌 <b>{data['category']}</b> › {day_type}\n\nChoose time slot:",
        reply_markup=adm_time_slots_keyboard("addcon", data["category"], day_type),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddContent.pick_time_slot), F.data.startswith("adm|addcon|ts|"))
async def add_con_pick_ts(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type, time_slot = parts
    await state.update_data(time_slot=time_slot)
    await state.set_state(AddContent.pick_group)
    await callback.message.edit_text(
        f"📌 › {day_type} › {time_slot}\n\nChoose group:",
        reply_markup=adm_group_names_keyboard("addcon", category, day_type, time_slot),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddContent.pick_group), F.data.startswith("adm|addcon|gn|"))
async def add_con_pick_group(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type, time_slot, group_name = parts
    await state.update_data(group_name=group_name)
    await state.set_state(AddContent.pick_section)
    await callback.message.edit_text(
        f"📌 › {group_name}\n\nChoose section:",
        reply_markup=adm_sections_keyboard("addcon", category, day_type, time_slot, group_name),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddContent.pick_section), F.data.startswith("adm|addcon|sec|"))
async def add_con_pick_section(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type, time_slot, group_name, section = parts
    await state.update_data(section=section)
    await state.set_state(AddContent.receive_content)
    await callback.message.edit_text(
        f"📥 Send the content for <b>{section}</b>.\n\n"
        "You can send: text, PDF, Word, photo, video, audio, voice.\n\n"
        "Send /cancel to abort."
    )
    await callback.answer()


@router.message(StateFilter(AddContent.receive_content))
async def add_con_receive(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    file_id = file_type = text = None
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
        await message.answer("⚠️ Unsupported type.")
        return

    new_id = add_content(
        category=data.get("category"),
        section=data.get("section"),
        text=text, file_id=file_id, file_type=file_type, caption=caption,
        day_type=data.get("day_type") or None,
        time_slot=data.get("time_slot") or None,
        group_name=data.get("group_name") or None,
    )
    await state.clear()
    await message.answer(
        f"✅ Saved! ID: <b>{new_id}</b>\n"
        f"Category: {data.get('category')} | Section: {data.get('section')}\n"
        f"Group: {data.get('group_name') or '—'} | Slot: {data.get('time_slot') or '—'}"
    )


# ══════════════ SHOW / DELETE CONTENT ══════════════

@router.message(Command("show_content"))
async def cmd_show_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(ShowContent.pick_category)
    await message.answer("🔎 Choose category:", reply_markup=adm_categories_keyboard("showcon"))


@router.callback_query(StateFilter(ShowContent.pick_category), F.data.startswith("adm|showcon|cat|"))
async def show_con_pick_cat(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split("|", 3)[3]
    await state.update_data(category=category, day_type="", time_slot="", group_name="")
    if category == GROUPS_CATEGORY:
        await state.set_state(ShowContent.pick_day_type)
        await callback.message.edit_text(
            f"🔎 <b>{category}</b>\n\nChoose day type:",
            reply_markup=adm_day_types_keyboard("showcon", category),
        )
    elif category == UNIVERSAL_CATEGORY:
        await state.set_state(ShowContent.pick_group)
        await callback.message.edit_text(
            f"🔎 <b>{category}</b>\n\nChoose group:",
            reply_markup=adm_group_names_keyboard("showcon", category),
        )
    else:
        await state.set_state(ShowContent.pick_section)
        await callback.message.edit_text(
            f"🔎 <b>{category}</b>\n\nChoose section:",
            reply_markup=adm_sections_keyboard("showcon", category),
        )
    await callback.answer()


@router.callback_query(StateFilter(ShowContent.pick_day_type), F.data.startswith("adm|showcon|dt|"))
async def show_con_pick_dt(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type = parts
    await state.update_data(day_type=day_type)
    await state.set_state(ShowContent.pick_time_slot)
    await callback.message.edit_text(
        f"🔎 › {day_type}\n\nChoose time slot:",
        reply_markup=adm_time_slots_keyboard("showcon", category, day_type),
    )
    await callback.answer()


@router.callback_query(StateFilter(ShowContent.pick_time_slot), F.data.startswith("adm|showcon|ts|"))
async def show_con_pick_ts(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type, time_slot = parts
    await state.update_data(time_slot=time_slot)
    await state.set_state(ShowContent.pick_group)
    await callback.message.edit_text(
        f"🔎 › {day_type} › {time_slot}\n\nChoose group:",
        reply_markup=adm_group_names_keyboard("showcon", category, day_type, time_slot),
    )
    await callback.answer()


@router.callback_query(StateFilter(ShowContent.pick_group), F.data.startswith("adm|showcon|gn|"))
async def show_con_pick_grp(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type, time_slot, group_name = parts
    await state.update_data(group_name=group_name)
    await state.set_state(ShowContent.pick_section)
    await callback.message.edit_text(
        f"🔎 › {group_name}\n\nChoose section:",
        reply_markup=adm_sections_keyboard("showcon", category, day_type, time_slot, group_name),
    )
    await callback.answer()


@router.callback_query(StateFilter(ShowContent.pick_section), F.data.startswith("adm|showcon|sec|"))
async def show_con_result(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("|")
    _, _, _, category, day_type, time_slot, group_name, section = parts
    await state.clear()
    rows = get_content(
        category=category, section=section,
        day_type=day_type or None, time_slot=time_slot or None,
        group_name=group_name or None,
    )
    if not rows:
        await callback.message.edit_text("📭 No content found.")
        await callback.answer()
        return
    lines = [f"📋 <b>{category} › {section}</b>\n"]
    for row in rows:
        kind = row["file_type"] or "text"
        preview = (row["text"] or row["caption"] or "")[:50].replace("\n", " ")
        lines.append(f"• <b>ID {row['id']}</b> [{kind}] {preview}")
    lines.append("\nUse /delete_content to remove.")
    await callback.message.edit_text("\n".join(lines))
    await callback.answer()


@router.message(Command("delete_content"))
async def cmd_delete_content(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(DeleteContent.waiting_id)
    await message.answer(
        "🗑 Send the <b>ID</b> to delete (from /show_content).\nSend /cancel to abort."
    )


@router.message(StateFilter(DeleteContent.waiting_id))
async def delete_con_by_id(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("⚠️ Send a numeric ID or /cancel.")
        return
    content_id = int(text)
    row = get_content_by_id(content_id)
    if not row:
        await message.answer(f"❌ No item with ID {content_id}.")
        await state.clear()
        return
    deleted = delete_content_by_id(content_id)
    await state.clear()
    if deleted:
        await message.answer(f"✅ Deleted ID {content_id}.")
    else:
        await message.answer("❌ Could not delete.")


# ══════════════ ANNOUNCEMENT ══════════════

@router.message(Command("announcement"))
async def cmd_announcement(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Admins only.")
        return
    await state.clear()
    await state.set_state(Announcement.waiting_text)
    await message.answer("📣 Send the announcement text.\nSend /cancel to abort.")


@router.message(StateFilter(Announcement.waiting_text))
async def send_announcement(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if not message.text:
        await message.answer("⚠️ Text only please, or /cancel.")
        return
    text = message.text.strip()
    add_announcement(text)
    user_ids = get_all_user_ids()
    await state.clear()
    sent = failed = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, f"📣 <b>Announcement</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Sent to {sent} students. Failed: {failed}.")
