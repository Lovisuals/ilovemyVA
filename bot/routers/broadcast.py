"bot/routers/broadcast.py"

import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.states.broadcast_states import BroadcastTargetSelection
from bot.services.bucket_service import BucketService
from bot.services.broadcast_service import BroadcastService
from bot.keyboards.broadcast_kb import build_target_selector
from bot.strings import BROADCAST_CONFIRMED, INVALID_ACTION

router = Router()

# Mock targets - in production these come from a DB table or config
LINKED_TARGETS = [
    {"chat_id": -100123456789, "name": "Main Channel"},
    {"chat_id": -100987654321, "name": "Locum Group"},
]

@router.callback_query(F.data.startswith("item_br:"))
async def on_broadcast_start(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    item_id = query.data.split(":")[1]
    await state.update_data(br_item_id=item_id, br_targets=[])
    await state.set_state(BroadcastTargetSelection.SELECTING_TARGETS)
    
    kb = build_target_selector(item_id, LINKED_TARGETS, [])
    await query.message.edit_text("Select targets for broadcast:", reply_markup=kb)
    await query.answer()

@router.callback_query(BroadcastTargetSelection.SELECTING_TARGETS, F.data.startswith("brd_t:"))
async def on_target_toggle(query: CallbackQuery, state: FSMContext):
    parts = query.data.split(":")
    item_id = parts[1]
    chat_id = int(parts[2])
    
    data = await state.get_data()
    selected = list(data["br_targets"])
    
    if chat_id in selected:
        selected.remove(chat_id)
    else:
        selected.append(chat_id)
        
    await state.update_data(br_targets=selected)
    kb = build_target_selector(item_id, LINKED_TARGETS, selected)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()

@router.callback_query(BroadcastTargetSelection.SELECTING_TARGETS, F.data.startswith("brd_d:"))
async def on_broadcast_done(
    query: CallbackQuery, 
    state: FSMContext, 
    bot: Bot, 
    session: AsyncSession
):
    data = await state.get_data()
    item_id = uuid.UUID(data["br_item_id"])
    target_ids = data["br_targets"]
    
    if not target_ids:
        await query.answer("Please select at least one target.")
        return

    item = await BucketService.get_by_id(session, item_id)
    if not item:
        await query.answer(INVALID_ACTION)
        return

    count = 0
    for target_id in target_ids:
        target_name = next((t["name"] for t in LINKED_TARGETS if t["chat_id"] == target_id), "Unknown")
        try:
            await BroadcastService.send(bot, session, item, target_id, target_name)
            count += 1
        except Exception:
            pass
            
    await query.message.edit_text(BROADCAST_CONFIRMED.format(count=count))
    await state.clear()
    await query.answer()
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
