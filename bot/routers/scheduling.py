import uuid
from datetime import datetime, time, timedelta
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
    await state.update_data(sch_item_id=item_id)
    await state.set_state(SchedulePicking.PICKING_TIME)

    kb = build_time_picker(item_id)
    await query.message.edit_text("Select a publication time (Africa/Lagos):", reply_markup=kb)
    await query.answer()

@router.callback_query(SchedulePicking.PICKING_TIME, ScheduleTime.filter())
async def on_time_picked(query: CallbackQuery, callback_data: ScheduleTime, state: FSMContext):
    item_id = callback_data.item_id
    time_str = callback_data.time_str

    await state.update_data(sch_time=time_str)
    await state.set_state(SchedulePicking.PICKING_RECURRENCE)

    kb = build_recurrence_picker(item_id)
    await query.message.edit_text(f"Time selected: {time_str}. Choose recurrence:", reply_markup=kb)
    await query.answer()

@router.callback_query(SchedulePicking.PICKING_RECURRENCE, ScheduleRecurrence.filter())
async def on_recurrence_picked(
    query: CallbackQuery,
    callback_data: ScheduleRecurrence,
    state: FSMContext,
    session: AsyncSession,
    bot: object
):
    recurrence = callback_data.recurrence
    data = await state.get_data()
    item_id = uuid.UUID(data["sch_item_id"])
    time_str = data["sch_time"]

    scheduler = bot.get("scheduler")
    if not scheduler:
        await query.answer("Scheduler not available.")
        return

    h, m = map(int, time_str.split(":"))
    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)
    run_at = tz.localize(datetime.combine(now.date(), time(h, m)))

    if run_at < now:
        run_at += timedelta(days=1)

    await SchedulerService.register_job(
        session, scheduler, item_id, run_at.astimezone(pytz.UTC), recurrence
    )

    await query.message.edit_text(
        SCHEDULE_CONFIRMED.format(time=run_at.strftime("%Y-%m-%d %H:%M"), recurrence=recurrence)
    )
    await state.clear()
    await query.answer()
