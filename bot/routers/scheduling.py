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
from bot.keyboards.schedule_kb import build_time_picker, build_recurrence_picker
from bot.strings import SCHEDULE_CONFIRMED, INVALID_ACTION
from bot.callbacks import ItemSchedule, ScheduleTime, ScheduleRecurrence

router = Router()

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

    if time_str in selected_times:
        selected_times.remove(time_str)
    else:
        selected_times.append(time_str)
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
    session: AsyncSession,
    scheduler: Any = None
):
    recurrence = callback_data.recurrence
    data = await state.get_data()
    item_id = uuid.UUID(data["sch_item_id"])
    times = data["sch_times"]

    if not scheduler:
        await query.answer("Scheduler not available.")
        return

    await SchedulerService.register_job(
        session, scheduler, item_id, times, recurrence
    )

    times_formatted = ", ".join(times)
    await query.message.edit_text(
        SCHEDULE_CONFIRMED.format(time=times_formatted, recurrence=recurrence)
    )
    await state.clear()
    await query.answer()
