import uuid
import json
from typing import Any
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks import ContentItemAction
from bot.keyboards.bucket_kb import build_bucket_list, build_content_list
from bot.keyboards.item_actions_kb import build_item_actions
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.content_service import ContentService
from bot.services.scheduler_service import SchedulerService
from bot.strings import BUCKET_TITLE, ITEM_VIEW
router = Router()
async def _safe_edit(query: CallbackQuery, text: str, reply_markup=None):
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        if "can't parse entities" in str(e):
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=None)
        else:
            raise
@router.message(Command("content"))
async def cmd_content(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    await message.answer(" Content Library\n\nSelect a bucket:", reply_markup=build_bucket_list())
@router.callback_query(ContentItemAction.filter())
async def on_item_action(
    query: CallbackQuery,
    callback_data: ContentItemAction,
    bot_user: BotUser,
    session: AsyncSession,
    scheduler: Any = None
):
    item_id = uuid.UUID(callback_data.item_id)
    action  = callback_data.action
    if action == "view":
        await query.answer()
        item = await ContentService.get_by_id(session, item_id)
        if item:
            kb = build_item_actions(str(item.id), item.bucket)
            text = ITEM_VIEW.format(text=item.text or "No text", bucket=item.bucket.value)
            if item.bucket == ContentBucket.SCHEDULED:
                sched_info = "\n\n"
                if item.sched_time:
                    times = item.sched_time.split(",")
                    sched_info += f"Time(s): {', '.join(times)}\n"
                if item.recurrence:
                    sched_info += f"Recurrence: {item.recurrence.capitalize()}\n"
                if item.target_chat_ids:
                    try:
                        targets = json.loads(item.target_chat_ids)
                        sched_info += f"Targets: {len(targets)} chats\n"
                    except Exception:
                        pass
                text += sched_info
            if item.subject:
                text = f"{item.subject}\n\n" + text
            await _safe_edit(query, text, reply_markup=kb)
    elif action == "unschedule":
        if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            await query.answer()
            return
        item = await ContentService.get_by_id(session, item_id)
        if item and item.bucket == ContentBucket.SCHEDULED:
            if item.scheduler_job_id and scheduler:
                await SchedulerService.cancel_job(scheduler, item.scheduler_job_id)
            item.bucket = ContentBucket.DRAFTS
            item.scheduler_job_id = None
            item.scheduled_at = None
            await session.commit()
            await query.answer("Item unscheduled and returned to drafts.")
            kb = build_item_actions(str(item.id), item.bucket)
            text = ITEM_VIEW.format(text=item.text or "No text", bucket=item.bucket.value)
            if item.subject:
                text = f" {item.subject}\n\n" + text
            await _safe_edit(query, text, reply_markup=kb)
        else:
            await query.answer("Item not scheduled.")
    elif action == "delete":
        if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            await query.answer()
            return
        await query.answer("Item deleted.")
        await ContentService.delete_item(session, item_id)
        kb = build_bucket_list()
        await _safe_edit(query, " Content Library\n\nSelect a bucket:", reply_markup=kb)
    elif action == "back":
        await query.answer()
        item = await ContentService.get_by_id(session, item_id)
        bucket = item.bucket if item else ContentBucket.DRAFTS
        items, total = await ContentService.get_page(session, bucket, 1, 10)
        kb = build_content_list(items, bucket, 1, max(1, (total + 9) // 10))
        await _safe_edit(query, BUCKET_TITLE.format(bucket=bucket.value), reply_markup=kb)
    else:
        await query.answer()
