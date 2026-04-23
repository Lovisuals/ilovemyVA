import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole
from bot.services.broadcast_service import BroadcastService
from bot.keyboards.broadcast_kb import build_target_selector
from bot.strings import BROADCAST_STARTED, INVALID_ACTION
from bot.config import settings

router = Router()

@router.callback_query(F.data.startswith("item_br:"))
async def on_broadcast_start(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    item_id = query.data.split(":")[1]
    targets = [{"name": "Main Channel", "chat_id": settings.bot.main_channel_id}]
    await state.update_data(br_item_id=item_id, br_targets=targets, br_selected=[])
    kb = build_target_selector(item_id, targets, [])
    await query.message.edit_text("Select broadcast targets:", reply_markup=kb)
    await query.answer()

@router.callback_query(F.data.startswith("br_tg:"))
async def on_target_toggle(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data["br_item_id"]
    targets = data["br_targets"]
    selected = data["br_selected"]
    chat_id = int(query.data.split(":")[2])
    if chat_id in selected:
        selected.remove(chat_id)
    else:
        selected.append(chat_id)
    await state.update_data(br_selected=selected)
    kb = build_target_selector(item_id, targets, selected)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()

@router.callback_query(F.data.startswith("br_dn:"))
async def on_broadcast_confirm(query: CallbackQuery, state: FSMContext, session: AsyncSession, bot: object):
    data = await state.get_data()
    item_id = uuid.UUID(data["br_item_id"])
    selected = data["br_selected"]
    if not selected:
        await query.answer("Please select at least one target.")
        return
    await BroadcastService.queue_broadcast(session, item_id, selected)
    await query.message.edit_text(BROADCAST_STARTED)
    await state.clear()
    await query.answer()
