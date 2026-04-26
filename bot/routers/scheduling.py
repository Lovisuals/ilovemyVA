import uuid
from datetime import datetime, time, timedelta
from typing import Any
import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.states.schedule_states import SchedulePicking
from bot.services.scheduler_service import SchedulerService
from bot.services.connected_chat_service import ConnectedChatService
from bot.keyboards.schedule_kb import build_time_picker, build_recurrence_picker
from bot.keyboards.draft_kb import build_target_kb
from bot.strings import SCHEDULE_CONFIRMED, INVALID_ACTION, DRAFT_TARGETS, DRAFT_NO_SELECTION
from bot.callbacks import ItemSchedule, ScheduleTime, ScheduleRecurrence, TargetToggle
import json

router = Router()

async def _get_chats(session: AsyncSession) -> list:
    chats = await ConnectedChatService.list_active(session)
    if not chats:
        from bot.models.connected_chat import ConnectedChat
        from bot.config import settings
        dummy = ConnectedChat.__new__(ConnectedChat)
        dummy.chat_id  = settings.bot.main_channel_id
        dummy.title    = "Main Channel"
        dummy.chat_type = "channel"
        return [dummy]
    return chats

@router.callback_query(ItemSchedule.filter())
async def on_schedule_start(query: CallbackQuery, callback_data: ItemSchedule, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    item_id = callback_data.item_id
    await state.update_data(sch_item_id=item_id, sch_times=[])
    await state.set_state(SchedulePicking.PICKING_TIME)

    kb = build_time_picker(item_id, [])
    await query.message.edit_text("Select publication time(s) (Africa/Lagos):", reply_markup=kb)
    await query.answer()

@router.callback_query(SchedulePicking.PICKING_TIME, ScheduleTime.filter())
async def on_time_picked(query: CallbackQuery, callback_data: ScheduleTime, state: FSMContext):
    item_id = callback_data.item_id
    time_str = callback_data.time_str

    data = await state.get_data()
    selected_times = data.get("sch_times", [])

    if time_str == "confirm":
        if not selected_times:
            await query.answer("Please select at least one time.", show_alert=True)
            return
        
        await state.update_data(sch_times=selected_times)
        await state.set_state(SchedulePicking.PICKING_RECURRENCE)

        kb = build_recurrence_picker(item_id)
        times_formatted = ", ".join(selected_times)
        await query.message.edit_text(f"Times selected: {times_formatted}. Choose recurrence:", reply_markup=kb)
        await query.answer()
        return

    clean_time = time_str if ":" in time_str else f"{time_str[:2]}:{time_str[2:]}"
    if clean_time in selected_times:
        selected_times.remove(clean_time)
    else:
        selected_times.append(clean_time)
        selected_times.sort()
        
    await state.update_data(sch_times=selected_times)
    
    kb = build_time_picker(item_id, selected_times)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()

@router.callback_query(SchedulePicking.PICKING_RECURRENCE, ScheduleRecurrence.filter())
async def on_recurrence_picked(
    query: CallbackQuery,
    callback_data: ScheduleRecurrence,
    state: FSMContext,
    session: AsyncSession
):
    recurrence = callback_data.recurrence
    await state.update_data(sch_recurrence=recurrence)
    
    chats = await _get_chats(session)
    all_ids = [c.chat_id for c in chats]
    await state.update_data(selected_ids=all_ids)
    await state.set_state(SchedulePicking.SELECTING_TARGETS)
    
    data = await state.get_data()
    times_formatted = ", ".join(data.get("sch_times", []))
    
    await query.message.edit_text(
        DRAFT_TARGETS.format(
            subject="Scheduling Draft",
            schedule_line=f"🔄 {recurrence.capitalize()} at {times_formatted}"
        ),
        reply_markup=build_target_kb(chats, all_ids, confirm_label="✅ Schedule")
    )
    await query.answer()

@router.callback_query(SchedulePicking.SELECTING_TARGETS, TargetToggle.filter(F.action == "chat"))
async def target_toggle(query: CallbackQuery, callback_data: TargetToggle, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected = list(data.get("selected_ids", []))
    cid = callback_data.chat_id
    if cid in selected: selected.remove(cid)
    else:               selected.append(cid)
    await state.update_data(selected_ids=selected)
    chats = await _get_chats(session)
    await query.message.edit_reply_markup(reply_markup=build_target_kb(chats, selected, confirm_label="✅ Schedule"))
    await query.answer()

@router.callback_query(SchedulePicking.SELECTING_TARGETS, TargetToggle.filter(F.action.in_({"all", "none"})))
async def target_all_none(query: CallbackQuery, callback_data: TargetToggle, state: FSMContext, session: AsyncSession):
    chats = await _get_chats(session)
    selected = [c.chat_id for c in chats] if callback_data.action == "all" else []
    await state.update_data(selected_ids=selected)
    await query.message.edit_reply_markup(reply_markup=build_target_kb(chats, selected, confirm_label="✅ Schedule"))
    await query.answer()

@router.callback_query(SchedulePicking.SELECTING_TARGETS, TargetToggle.filter(F.action == "confirm"))
async def target_confirm(
    query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    scheduler: Any = None
):
    data = await state.get_data()
    selected_ids = data.get("selected_ids", [])
    if not selected_ids:
        await query.answer(DRAFT_NO_SELECTION, show_alert=True)
        return

    item_id = uuid.UUID(data["sch_item_id"])
    times = data["sch_times"]
    recurrence = data["sch_recurrence"]

    if not scheduler:
        await query.answer("Scheduler not available.")
        return

    from bot.models.content_item import ContentItem
    result = await session.execute(select(ContentItem).where(ContentItem.id == item_id))
    item = result.scalar_one_or_none()
    if item:
        item.target_chat_ids = json.dumps(selected_ids)
        await session.commit()

    await SchedulerService.register_job(session, scheduler, item_id, times, recurrence)
    
    times_formatted = ", ".join(times)
    await query.message.edit_text(SCHEDULE_CONFIRMED.format(time=times_formatted, recurrence=recurrence))
    await state.clear()
    await query.answer("Scheduled!")
