import json
import logging
import re
import uuid
from aiohttp import web
from datetime import datetime, timedelta, timezone
from typing import List
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks import (
    DayToggle, NavData, PostAction, RetryBroadcast, SchedType, TargetToggle, TimeSlot, MultiTimeToggle
)
from bot.config import settings
from bot.keyboards.draft_kb import (
    build_action_kb, build_custom_time_kb, build_datetime_kb, build_day_kb,
    build_report_kb, build_sched_type_kb, build_step1_kb, build_step2_kb,
    build_target_kb, build_time_kb, build_multi_time_kb
)
from bot.keyboards.menu_kb import build_main_menu, build_menu_row
from bot.models.bot_user import BotUser, UserRole
from bot.models.broadcast_log import BroadcastLog, BroadcastStatus
from bot.models.content_item import ContentBucket
from bot.services.connected_chat_service import ConnectedChatService
from bot.services.content_service import ContentService
from bot.services.persona_service import PersonaService
from bot.utils.debug_log import write_debug_log
from bot.states.draft_states import DraftCreation
from bot.strings import (
    DRAFT_CUSTOM_TIME, DRAFT_CUSTOM_TIME_ERROR, DRAFT_DAY_PICK,
    DRAFT_DATETIME_ERROR, DRAFT_DATETIME_PICK, DRAFT_NO_SELECTION,
    DRAFT_PREVIEW, DRAFT_REPORT_FOOTER, DRAFT_REPORT_HEADER,
    DRAFT_REPORT_ROW_FAIL, DRAFT_REPORT_ROW_OK, DRAFT_SAVED, DRAFT_SCHED_TYPE,
    DRAFT_SCHEDULED_ONCE, DRAFT_SCHEDULED_RECURRING, DRAFT_STEP1,
    DRAFT_STEP1_ERROR, DRAFT_STEP2, DRAFT_TARGETS, DRAFT_TIME_PICK, MENU_ADMIN,
)
logger = logging.getLogger(__name__)
router = Router()
_ALL_DAYS  = ["mo", "tu", "we", "th", "fr", "sa", "su"]
_WEEKDAYS  = ["mo", "tu", "we", "th", "fr"]
_WEEKENDS  = ["sa", "su"]
_DAY_LABELS = {
    "mo": "Mon", "tu": "Tue", "we": "Wed", "th": "Thu",
    "fr": "Fri", "sa": "Sat", "su": "Sun",
}
_TIME_LABELS = {
    "always": "always", "0600": "06:00", "0900": "09:00",
    "1200": "12:00",    "1500": "15:00", "1800": "18:00", "2100": "21:00",
}
def _days_text(days: List[str]) -> str:
    if sorted(days) == sorted(_ALL_DAYS):   return "every day"
    if sorted(days) == sorted(_WEEKDAYS):   return "weekdays"
    if sorted(days) == sorted(_WEEKENDS):   return "weekends"
    return ", ".join(_DAY_LABELS.get(d, d) for d in days)
async def _edit(bot: Bot, chat_id: int, msg_id: int, text: str, markup) -> None:
    try:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, text=text, reply_markup=markup
        )
    except Exception:
        pass
async def _safe_delete(msg: Message) -> None:
    try:
        await msg.delete()
    except TelegramBadRequest:
        pass
async def _get_chats(session: AsyncSession) -> list:
    chats = await ConnectedChatService.list_active(session)
    if not chats:
        from bot.models.connected_chat import ConnectedChat
        dummy = ConnectedChat.__new__(ConnectedChat)
        dummy.chat_id  = settings.bot.main_channel_id
        dummy.title    = "Main Channel"
        dummy.chat_type = "channel"
        return [dummy]
    return chats
def _build_report(results: list, chats_by_id: dict) -> str:
    rows = []
    for r in results:
        title = chats_by_id.get(r["chat_id"], str(r["chat_id"]))
        if r["success"]:
            rows.append(DRAFT_REPORT_ROW_OK.format(title=title))
        else:
            rows.append(DRAFT_REPORT_ROW_FAIL.format(title=title, error=r.get("error", "")[:80]))
    sent   = sum(1 for r in results if r["success"])
    failed = len(results) - sent
    return DRAFT_REPORT_HEADER + "\n".join(rows) + DRAFT_REPORT_FOOTER.format(sent=sent, failed=failed)
async def _do_send(
    bot: Bot, session: AsyncSession, item_id, text: str,
    selected_ids: List[int], chats_by_id: dict,
) -> list:
    import asyncio
    sem = asyncio.Semaphore(5)
    async def _send_one(chat_id: int):
        async with sem:
            from bot.models.connected_chat import ConnectedChat
            chat_info = await session.get(ConnectedChat, chat_id)
            thread_id = chat_info.message_thread_id if chat_info else None
            log = BroadcastLog(
                content_id=item_id,
                target_chat_id=chat_id,
                target_name=chats_by_id.get(chat_id, ""),
                status=BroadcastStatus.PENDING,
            )
            session.add(log)
            try:
                msg = await bot.send_message(
                    chat_id, text,
                    message_thread_id=thread_id
                )
                log.status    = BroadcastStatus.SENT
                log.message_id = msg.message_id
                log.sent_at   = datetime.now(timezone.utc)
                return {"chat_id": chat_id, "success": True}
            except Exception as exc:
                log.status       = BroadcastStatus.FAILED
                log.error_detail = str(exc)[:200]
                return {"chat_id": chat_id, "success": False, "error": str(exc)[:80]}
    results = await asyncio.gather(*(_send_one(cid) for cid in selected_ids))
    if item_id:
        await session.commit()
    return list(results)
@router.message(F.web_app_data, F.chat.type == "private")
async def on_editor_data(message: Message, state: FSMContext, bot: Bot):
    await _safe_delete(message)
    try:
        payload = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        return
    subject = (payload.get("subject") or "").strip()
    body    = (payload.get("body") or "").strip()
    if not body:
        return
    fsm_data = await state.get_data()
    if not fsm_data.get("draft_msg_id"):
        sent = await bot.send_message(message.chat.id, DRAFT_STEP1, reply_markup=build_step1_kb())
        await state.update_data(draft_msg_id=sent.message_id, draft_chat_id=message.chat.id)
        fsm_data = await state.get_data()
    await state.update_data(subject=subject, body=body)
    await state.set_state(DraftCreation.CHOOSING_ACTION)
    preview_body = body[:600] + ("…" if len(body) > 600 else "")
    await _edit(
        bot, fsm_data["draft_chat_id"], fsm_data["draft_msg_id"],
        DRAFT_PREVIEW.format(subject=subject, body=preview_body),
        build_action_kb(),
    )
@router.message(Command("new"))
async def cmd_new(message: Message, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        return
    sent = await message.answer(DRAFT_STEP1, reply_markup=build_step1_kb())
    await state.set_state(DraftCreation.WAITING_SUBJECT)
    await state.update_data(draft_msg_id=sent.message_id, draft_chat_id=message.chat.id)
@router.callback_query(NavData.filter(F.section == "new"))
async def nav_new(query: CallbackQuery, bot_user: BotUser, state: FSMContext, bot: Bot):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await _edit(bot, query.message.chat.id, query.message.message_id, DRAFT_STEP1, build_step1_kb())
    await state.set_state(DraftCreation.WAITING_SUBJECT)
    await state.update_data(
        draft_msg_id=query.message.message_id,
        draft_chat_id=query.message.chat.id,
    )
    await query.answer()
@router.callback_query(PostAction.filter(F.action == "type_mode"))
async def switch_to_type_mode(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.WAITING_SUBJECT)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_STEP1, build_step2_kb())
    await query.answer()
@router.message(DraftCreation.WAITING_SUBJECT, F.text, F.chat.type == "private")
async def on_subject(message: Message, state: FSMContext, bot: Bot):
    subject = (message.text or "").strip()
    data = await state.get_data()
    await _safe_delete(message)
    if not subject:
        return
    if len(subject) > 256:
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_STEP1_ERROR.format(error="Subject too long (max 256 characters)."),
                    build_step1_kb())
        return
    await state.update_data(subject=subject)
    await state.set_state(DraftCreation.WAITING_BODY)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_STEP2.format(subject=subject), build_step2_kb())
@router.message(DraftCreation.WAITING_BODY, F.text, F.chat.type == "private")
async def on_body(message: Message, state: FSMContext, bot: Bot):
    body = (message.text or "").strip()
    data = await state.get_data()
    await _safe_delete(message)
    if not body:
        return
    await state.update_data(body=body)
    await state.set_state(DraftCreation.CHOOSING_ACTION)
    subject     = data.get("subject", "")
    preview_body = body[:600] + ("…" if len(body) > 600 else "")
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_PREVIEW.format(subject=subject, body=preview_body), build_action_kb())
@router.callback_query(PostAction.filter(F.action == "edit_subj"),
                       DraftCreation.WAITING_BODY)
@router.callback_query(PostAction.filter(F.action == "edit_subj"),
                       DraftCreation.CHOOSING_ACTION)
async def edit_subject(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    current = data.get("subject", "")
    hint = f"\n\nCurrent: {current}\nSend a new headline to replace it." if current else ""
    await state.set_state(DraftCreation.WAITING_SUBJECT)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_STEP1 + hint, build_step1_kb())
    await query.answer()
@router.callback_query(PostAction.filter(F.action == "edit_body"),
                       DraftCreation.CHOOSING_ACTION)
async def edit_body(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    subject = data.get("subject", "")
    await state.set_state(DraftCreation.WAITING_BODY)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_STEP2.format(subject=subject) + "\n\nSend new content to replace current body.",
                build_step2_kb())
    await query.answer()
@router.callback_query(PostAction.filter(F.action == "cancel"))
async def post_cancel(query: CallbackQuery, state: FSMContext, bot_user: BotUser, bot: Bot):
    await state.clear()
    await _edit(bot, query.message.chat.id, query.message.message_id,
                MENU_ADMIN, build_main_menu(bot_user.role))
    await query.answer()
@router.callback_query(PostAction.filter(F.action == "draft"), DraftCreation.CHOOSING_ACTION)
async def post_save_draft(
    query: CallbackQuery, state: FSMContext, session: AsyncSession, bot_user: BotUser, bot: Bot
):
    data = await state.get_data()
    await ContentService.create_item(
        session,
        bucket=ContentBucket.DRAFTS,
        text=data.get("body", ""),
        subject=data.get("subject") or None,
        post_type="draft",
        created_by=bot_user.id,
    )
    await state.clear()
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"], DRAFT_SAVED, build_menu_row())
    await query.answer("Draft saved.")
@router.callback_query(PostAction.filter(F.action == "now"), DraftCreation.CHOOSING_ACTION)
async def post_now(query: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data  = await state.get_data()
    chats = await _get_chats(session)
    all_ids = [c.chat_id for c in chats]
    await state.update_data(post_type="post_now", selected_ids=all_ids, back_to="action")
    await state.set_state(DraftCreation.SELECTING_TARGETS)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_TARGETS.format(subject=data.get("subject", ""),
                                     schedule_line=" Sends immediately"),
                build_target_kb(chats, all_ids, confirm_label=" Send Now"))
    await query.answer()
@router.callback_query(PostAction.filter(F.action == "sched"), DraftCreation.CHOOSING_ACTION)
async def post_sched(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.CHOOSING_SCHED_TYPE)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_SCHED_TYPE.format(subject=data.get("subject", "")), build_sched_type_kb())
    await query.answer()
@router.callback_query(SchedType.filter(F.sched_type == "back"), DraftCreation.CHOOSING_SCHED_TYPE)
async def sched_type_back(query: CallbackQuery, state: FSMContext, bot: Bot):
    data        = await state.get_data()
    subject     = data.get("subject", "")
    body        = data.get("body", "")
    preview_body = body[:600] + ("…" if len(body) > 600 else "")
    await state.set_state(DraftCreation.CHOOSING_ACTION)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_PREVIEW.format(subject=subject, body=preview_body), build_action_kb())
    await query.answer()
@router.callback_query(SchedType.filter(F.sched_type == "recurring"), DraftCreation.CHOOSING_SCHED_TYPE)
async def sched_recurring(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(post_type="recurring")
    await state.set_state(DraftCreation.CHOOSING_TIME)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_TIME_PICK.format(subject=data.get("subject", "")), build_time_kb())
    await query.answer()
@router.callback_query(SchedType.filter(F.sched_type == "one_time"), DraftCreation.CHOOSING_SCHED_TYPE)
async def sched_one_time(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(post_type="one_time")
    await state.set_state(DraftCreation.ENTERING_DATETIME)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_DATETIME_PICK.format(subject=data.get("subject", "")), build_datetime_kb())
    await query.answer()
@router.callback_query(SchedType.filter(F.sched_type == "back"), DraftCreation.ENTERING_DATETIME)
async def datetime_back(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.CHOOSING_SCHED_TYPE)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_SCHED_TYPE.format(subject=data.get("subject", "")), build_sched_type_kb())
    await query.answer()
@router.message(DraftCreation.ENTERING_DATETIME, F.text, F.chat.type == "private")
async def on_datetime(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    text = (message.text or "").strip()
    data = await state.get_data()
    await _safe_delete(message)
    try:
        dt = datetime.strptime(text, "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_DATETIME_ERROR.format(error="Invalid format. Use DD/MM/YYYY HH:MM"),
                    build_datetime_kb())
        return
    if dt < datetime.now(timezone.utc) + timedelta(minutes=1):
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_DATETIME_ERROR.format(error="Must be at least 1 minute in the future."),
                    build_datetime_kb())
        return
    chats   = await _get_chats(session)
    all_ids = [c.chat_id for c in chats]
    await state.update_data(sched_dt=text, selected_ids=all_ids, back_to="datetime")
    await state.set_state(DraftCreation.SELECTING_TARGETS)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_TARGETS.format(subject=data.get("subject", ""),
                                     schedule_line=f" One-time: {text}"),
                build_target_kb(chats, all_ids, confirm_label=" Schedule"))
@router.callback_query(TimeSlot.filter(F.slot == "back"), DraftCreation.CHOOSING_TIME)
async def time_back(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.CHOOSING_SCHED_TYPE)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_SCHED_TYPE.format(subject=data.get("subject", "")), build_sched_type_kb())
    await query.answer()
@router.callback_query(TimeSlot.filter(F.slot == "custom"), DraftCreation.CHOOSING_TIME)
async def time_custom(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.ENTERING_CUSTOM_TIME)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_CUSTOM_TIME.format(subject=data.get("subject", "")), build_custom_time_kb())
    await query.answer()
@router.callback_query(TimeSlot.filter(), DraftCreation.CHOOSING_TIME)
async def time_selected(query: CallbackQuery, callback_data: TimeSlot, state: FSMContext, bot: Bot):
    slot = callback_data.slot
    if slot in ("back", "custom"):
        return
    data = await state.get_data()
    if slot == "always":
        await state.update_data(selected_times=[])
        await state.set_state(DraftCreation.CHOOSING_MULTIPLE_TIMES)
        await _edit(bot, query.message.chat.id, query.message.message_id,
                    "Select multiple time intervals for this broadcast:",
                    build_multi_time_kb([]))
        await query.answer()
        return
    human     = _TIME_LABELS.get(slot, slot)
    sched_time = f"{slot[:2]}:{slot[2:]}"
    await state.update_data(sched_time=sched_time, selected_days=list(_ALL_DAYS))
    await state.set_state(DraftCreation.CHOOSING_DAYS)
    await _edit(bot, query.message.chat.id, query.message.message_id,
                DRAFT_DAY_PICK.format(subject=data.get("subject", ""), time_text=human),
                build_day_kb(list(_ALL_DAYS)))
    await query.answer()
@router.callback_query(MultiTimeToggle.filter(), DraftCreation.CHOOSING_MULTIPLE_TIMES)
async def multi_time_toggle(query: CallbackQuery, callback_data: MultiTimeToggle, state: FSMContext, bot: Bot):
    try:
        action = callback_data.action
        data = await state.get_data()
        msg = query.message
        if not msg:
            await query.answer("Interaction error: Message not found.")
            return
        if action == "back":
            await state.set_state(DraftCreation.CHOOSING_TIME)
            await _edit(bot, msg.chat.id, msg.message_id,
                        DRAFT_TIME_PICK.format(subject=data.get("subject", "")), build_time_kb())
            await query.answer()
            return
        selected_times = list(data.get("selected_times", []))
        if action == "toggle":
            slot = callback_data.slot
            if slot in selected_times:
                selected_times.remove(slot)
            else:
                selected_times.append(slot)
            await state.update_data(selected_times=selected_times)
            count = len(selected_times)
            formatted = ", ".join(sorted(selected_times))
            text = f"Select multiple time intervals for this broadcast:\nSelected ({count}): {formatted if formatted else 'None'}"
            try:
                await msg.edit_text(text, reply_markup=build_multi_time_kb(selected_times))
            except TelegramBadRequest:
                pass
            await query.answer()
            return
        if action == "confirm":
            if not selected_times:
                await query.answer("Select at least one time.", show_alert=True)
                return
            formatted_times = []
            for s in sorted(selected_times):
                if len(s) == 4:
                    formatted_times.append(f"{s[:2]}:{s[2:]}")
                else:
                    formatted_times.append(s)
            sched_time = ",".join(formatted_times)
            await state.update_data(sched_time=sched_time, selected_days=list(_ALL_DAYS))
            await state.set_state(DraftCreation.CHOOSING_DAYS)
            time_text = ", ".join(formatted_times)
            if len(time_text) > 40:
                time_text = time_text[:37] + "..."
            await _edit(bot, msg.chat.id, msg.message_id,
                        DRAFT_DAY_PICK.format(subject=data.get("subject", ""), time_text=time_text),
                        build_day_kb(list(_ALL_DAYS)))
            await query.answer()
    except Exception as exc:
        logger.exception("Error in multi_time_toggle: %s", exc)
        await query.answer(f"Error: {str(exc)[:100]}", show_alert=True)
@router.callback_query(TimeSlot.filter(F.slot == "back"), DraftCreation.ENTERING_CUSTOM_TIME)
async def custom_time_back(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.CHOOSING_TIME)
    await _edit(bot, query.message.chat.id, query.message.message_id,
                DRAFT_TIME_PICK.format(subject=data.get("subject", "")), build_time_kb())
    await query.answer()
@router.message(DraftCreation.ENTERING_CUSTOM_TIME, F.text, F.chat.type == "private")
async def on_custom_time(message: Message, state: FSMContext, bot: Bot):
    text = (message.text or "").strip()
    data = await state.get_data()
    await _safe_delete(message)
    if not re.fullmatch(r"\d{1,2}:\d{2}", text):
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_CUSTOM_TIME_ERROR.format(error="Invalid format. Use HH:MM (e.g. 14:30)"),
                    build_custom_time_kb())
        return
    h, m = map(int, text.split(":"))
    if not (0 <= h <= 23 and 0 <= m <= 59):
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_CUSTOM_TIME_ERROR.format(error="Invalid value. Hours 0-23, minutes 0-59."),
                    build_custom_time_kb())
        return
    sched_time = f"{h:02d}:{m:02d}"
    await state.update_data(sched_time=sched_time, selected_days=list(_ALL_DAYS))
    await state.set_state(DraftCreation.CHOOSING_DAYS)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_DAY_PICK.format(subject=data.get("subject", ""), time_text=sched_time),
                build_day_kb(list(_ALL_DAYS)))
@router.callback_query(DayToggle.filter(F.day == "back"), DraftCreation.CHOOSING_DAYS)
async def days_back(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.set_state(DraftCreation.CHOOSING_TIME)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_TIME_PICK.format(subject=data.get("subject", "")), build_time_kb())
    await query.answer()
@router.callback_query(DayToggle.filter(F.day == "confirm"), DraftCreation.CHOOSING_DAYS)
async def days_confirm(query: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data          = await state.get_data()
    selected_days = data.get("selected_days", list(_ALL_DAYS))
    if not selected_days:
        await query.answer("Select at least one day.", show_alert=True)
        return
    chats   = await _get_chats(session)
    all_ids = [c.chat_id for c in chats]
    time_text   = data.get("sched_time", "always")
    days_label  = _days_text(selected_days)
    await state.update_data(selected_ids=all_ids, back_to="days")
    await state.set_state(DraftCreation.SELECTING_TARGETS)
    await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                DRAFT_TARGETS.format(subject=data.get("subject", ""),
                                     schedule_line=f" Every {days_label} at {time_text}"),
                build_target_kb(chats, all_ids, confirm_label=" Schedule"))
    await query.answer()
@router.callback_query(DayToggle.filter(), DraftCreation.CHOOSING_DAYS)
async def day_toggle(query: CallbackQuery, callback_data: DayToggle, state: FSMContext):
    day      = callback_data.day
    data     = await state.get_data()
    selected = list(data.get("selected_days", list(_ALL_DAYS)))
    if   day == "everyday": selected = list(_ALL_DAYS)
    elif day == "weekdays": selected = list(_WEEKDAYS)
    elif day == "weekends": selected = list(_WEEKENDS)
    elif day in _DAY_LABELS:
        if day in selected: selected.remove(day)
        else:               selected.append(day)
    else:
        await query.answer()
        return
    await state.update_data(selected_days=selected)
    time_text = data.get("sched_time", "always")
    count = len(selected)
    try:
        await query.message.edit_text(
            DRAFT_DAY_PICK.format(subject=data.get("subject", ""), time_text=time_text) + f"\nSelected ({count}d): " + _days_text(selected),
            reply_markup=build_day_kb(selected),
        )
    except TelegramBadRequest:
        pass
    await query.answer()
@router.callback_query(TargetToggle.filter(F.action == "back"), DraftCreation.SELECTING_TARGETS)
async def targets_back(query: CallbackQuery, state: FSMContext, bot: Bot):
    data    = await state.get_data()
    subject = data.get("subject", "")
    back_to = data.get("back_to", "action")
    if back_to == "days":
        selected_days = data.get("selected_days", list(_ALL_DAYS))
        await state.set_state(DraftCreation.CHOOSING_DAYS)
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_DAY_PICK.format(subject=subject,
                                         time_text=data.get("sched_time", "always")),
                    build_day_kb(selected_days))
    elif back_to == "datetime":
        await state.set_state(DraftCreation.ENTERING_DATETIME)
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_DATETIME_PICK.format(subject=subject), build_datetime_kb())
    else:
        body        = data.get("body", "")
        preview_body = body[:600] + ("…" if len(body) > 600 else "")
        await state.set_state(DraftCreation.CHOOSING_ACTION)
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_PREVIEW.format(subject=subject, body=preview_body), build_action_kb())
    await query.answer()
@router.callback_query(TargetToggle.filter(F.action == "chat"), DraftCreation.SELECTING_TARGETS)
async def target_toggle(
    query: CallbackQuery, callback_data: TargetToggle, state: FSMContext, session: AsyncSession
):
    data     = await state.get_data()
    selected = list(data.get("selected_ids", []))
    cid      = callback_data.chat_id
    if cid in selected: selected.remove(cid)
    else:               selected.append(cid)
    await state.update_data(selected_ids=selected)
    chats         = await _get_chats(session)
    confirm_label = " Send Now" if data.get("post_type") == "post_now" else " Schedule"
    try:
        await query.message.edit_reply_markup(
            reply_markup=build_target_kb(chats, selected, confirm_label=confirm_label)
        )
    except TelegramBadRequest:
        pass
    await query.answer()
@router.callback_query(
    TargetToggle.filter(F.action.in_({"all", "none"})), DraftCreation.SELECTING_TARGETS
)
async def target_all_none(
    query: CallbackQuery, callback_data: TargetToggle, state: FSMContext, session: AsyncSession
):
    data          = await state.get_data()
    chats         = await _get_chats(session)
    selected      = [c.chat_id for c in chats] if callback_data.action == "all" else []
    confirm_label = " Send Now" if data.get("post_type") == "post_now" else " Schedule"
    await state.update_data(selected_ids=selected)
    try:
        await query.message.edit_reply_markup(
            reply_markup=build_target_kb(chats, selected, confirm_label=confirm_label)
        )
    except TelegramBadRequest:
        pass
    await query.answer()
@router.callback_query(TargetToggle.filter(F.action == "confirm"), DraftCreation.SELECTING_TARGETS)
async def targets_confirm(
    query: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot, bot_user: BotUser
):
    data         = await state.get_data()
    selected_ids = data.get("selected_ids", [])
    if not selected_ids:
        await query.answer(DRAFT_NO_SELECTION, show_alert=True)
        return
    subject   = data.get("subject", "")
    body      = data.get("body", "")
    post_type = data.get("post_type", "post_now")
    chats        = await _get_chats(session)
    chats_by_id  = {c.chat_id: c.title for c in chats}
    persona      = await PersonaService.get_active(session)
    if post_type == "post_now":
        sep      = "─" * 28
        header   = f"{subject}\n{sep}\n" if subject else ""
        raw_text = header + body
        final    = PersonaService.apply_to_text(raw_text, persona)
        item = await ContentService.create_item(
            session,
            bucket=ContentBucket.PUBLISHED,
            text=body,
            subject=subject or None,
            post_type="post_now",
            target_chat_ids=json.dumps(selected_ids),
            created_by=bot_user.id,
        )
        await query.answer("Sending…")
        results    = await _do_send(bot, session, item.id, final, selected_ids, chats_by_id)
        failed_ids = [r["chat_id"] for r in results if not r["success"]]
        if failed_ids:
            await state.update_data(retry_text=final, retry_ids=failed_ids)
        else:
            await state.clear()
        try:
            await query.message.edit_text(
                _build_report(results, chats_by_id),
                reply_markup=build_report_kb(bool(failed_ids)),
            )
        except TelegramBadRequest:
            pass
    elif post_type == "recurring":
        sched_days = data.get("selected_days", list(_ALL_DAYS))
        sched_time = data.get("sched_time", "always")
        days_label = _days_text(sched_days)
        await ContentService.create_item(
            session,
            bucket=ContentBucket.SCHEDULED,
            text=body,
            subject=subject or None,
            post_type="recurring",
            sched_days=",".join(sched_days),
            sched_time=sched_time,
            target_chat_ids=json.dumps(selected_ids),
            created_by=bot_user.id,
        )
        await state.clear()
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_SCHEDULED_RECURRING.format(
                        subject=subject, days_text=days_label,
                        time_text=sched_time, target_count=len(selected_ids),
                    ), build_menu_row())
        await query.answer("Scheduled!")
    elif post_type == "one_time":
        sched_dt_str = data.get("sched_dt", "")
        try:
            sched_dt = datetime.strptime(sched_dt_str, "%d/%m/%Y %H:%M")
        except ValueError:
            sched_dt = None
        await ContentService.create_item(
            session,
            bucket=ContentBucket.SCHEDULED,
            text=body,
            subject=subject or None,
            post_type="one_time",
            scheduled_at=sched_dt,
            target_chat_ids=json.dumps(selected_ids),
            created_by=bot_user.id,
        )
        await state.clear()
        await _edit(bot, data["draft_chat_id"], data["draft_msg_id"],
                    DRAFT_SCHEDULED_ONCE.format(
                        subject=subject, datetime_text=sched_dt_str,
                        target_count=len(selected_ids),
                    ), build_menu_row())
        await query.answer("Scheduled!")
@router.callback_query(RetryBroadcast.filter())
async def retry_broadcast(
    query: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot
):
    data       = await state.get_data()
    retry_text = data.get("retry_text", "")
    retry_ids  = data.get("retry_ids", [])
    if not retry_text or not retry_ids:
        await state.clear()
        await query.answer("Nothing to retry.", show_alert=True)
        return
    chats       = await _get_chats(session)
    chats_by_id = {c.chat_id: c.title for c in chats}
    await query.answer("Retrying…")
    results    = await _do_send(bot, session, None, retry_text, retry_ids, chats_by_id)
    still_bad  = [r["chat_id"] for r in results if not r["success"]]
    if still_bad:
        await state.update_data(retry_ids=still_bad)
    else:
        await state.clear()
    try:
        await query.message.edit_text(
            _build_report(results, chats_by_id),
            reply_markup=build_report_kb(bool(still_bad)),
        )
    except TelegramBadRequest:
        pass
from aiohttp import web
import hmac
import hashlib
from urllib.parse import parse_qsl
def verify_init_data(token: str, init_data: str):
    try:
        write_debug_log(
            run_id="pre-fix",
            hypothesis_id="H10",
            location="bot/routers/drafting.py:verify_init_data",
            message="Verifying Telegram initData",
            data={"has_init_data": bool(init_data), "init_data_len": len(init_data or "")},
        )
        parsed_data = dict(parse_qsl(init_data or ""))
        if "hash" not in parsed_data:
            write_debug_log(
                run_id="pre-fix",
                hypothesis_id="H10",
                location="bot/routers/drafting.py:verify_init_data",
                message="initData missing hash",
                data={},
            )
            return None
        hash_val = parsed_data.pop("hash")
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        if calculated_hash != hash_val:
            write_debug_log(
                run_id="pre-fix",
                hypothesis_id="H10",
                location="bot/routers/drafting.py:verify_init_data",
                message="initData hash mismatch",
                data={"calculated_prefix": calculated_hash[:12], "received_prefix": hash_val[:12]},
            )
            return None
        if "user" in parsed_data:
            return json.loads(parsed_data["user"])
    except Exception as e:
        write_debug_log(
            run_id="pre-fix",
            hypothesis_id="H10",
            location="bot/routers/drafting.py:verify_init_data",
            message="Exception while verifying initData",
            data={"error": str(e)},
        )
        pass
    return None
async def api_get_item_handler(request: web.Request) -> web.Response:
    item_id_str = request.match_info.get("item_id")
    init_data = request.query.get("initData")
    user = verify_init_data(settings.bot.token, init_data)
    if not user:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        item_id = uuid.UUID(item_id_str)
    except (ValueError, TypeError):
        return web.json_response({"ok": False, "error": "Invalid item_id"}, status=400)
    from database.session import async_session
    from bot.services.bucket_service import BucketService
    async with async_session() as session:
        item = await BucketService.get_by_id(session, item_id)
        if not item:
            return web.json_response({"ok": False, "error": "Item not found"}, status=404)
        return web.json_response({
            "ok": True,
            "subject": item.subject or "",
            "body": item.text or "",
            "bucket": item.bucket.value
        })
async def api_draft_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON"}, status=400)
    init_data = data.get("initData")
    payload = data.get("payload", {})
    item_id_str = data.get("item_id")
    user = verify_init_data(settings.bot.token, init_data)
    if not user:
        return web.json_response({"ok": False, "error": "Unauthorized. Please close and reopen the editor."}, status=401)
    user_id = user.get("id")
    if not user_id:
        return web.json_response({"ok": False, "error": "No user ID"}, status=401)
    subject = (payload.get("subject") or "").strip()
    body    = (payload.get("body") or "").strip()
    if not body:
        return web.json_response({"ok": False, "error": "Empty body"}, status=400)
    if item_id_str:
        try:
            item_id = uuid.UUID(item_id_str)
            from database.session import async_session
            from bot.services.bucket_service import BucketService
            from bot.services.agent_service import AgentService
            async with async_session() as session:
                item = await BucketService.get_by_id(session, item_id)
                if item:
                    item.subject = subject or None
                    item.text = body
                    tone_result = await AgentService.run_tone_check(body)
                    item.tone_score = tone_result.score
                    item.tone_flags = tone_result.flags
                    # SIDE EFFECT: Updates existing content item from Web App. Why necessary and unavoidable: Enables seamless sync between Web App editor and bot storage.
                    await session.commit()
        except Exception as e:
            logger.error("API: failed to update item %s: %s", item_id_str, e)
    from aiogram.fsm.storage.base import StorageKey
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    dp = request.app["dispatcher"]
    state = FSMContext(storage=dp.storage, key=key)
    fsm_data = await state.get_data()
    if not fsm_data.get("draft_msg_id"):
        sent = await bot.send_message(user_id, DRAFT_STEP1, reply_markup=build_step1_kb())
        await state.update_data(draft_msg_id=sent.message_id, draft_chat_id=user_id)
        fsm_data = await state.get_data()
    await state.update_data(subject=subject, body=body)
    await state.set_state(DraftCreation.CHOOSING_ACTION)
    preview_body = body[:600] + ("…" if len(body) > 600 else "")
    await _edit(
        bot, fsm_data["draft_chat_id"], fsm_data["draft_msg_id"],
        DRAFT_PREVIEW.format(subject=subject, body=preview_body),
        build_action_kb(),
    )
    return web.json_response({"ok": True})
