import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import BroadcastDone, BroadcastToggle
from bot.config import settings
from bot.keyboards.broadcast_kb import build_target_selector
from bot.keyboards.menu_kb import build_menu_row
from bot.models.bot_user import BotUser, UserRole
from bot.models.broadcast_log import BroadcastLog, BroadcastStatus
from bot.models.content_item import ContentItem
from bot.services.connected_chat_service import ConnectedChatService
from bot.services.persona_service import PersonaService
from bot.strings import BROADCAST_NO_PERSONA, BROADCAST_SENT, INVALID_ACTION

router = Router()


async def _get_targets(session: AsyncSession) -> list:
    """Returns connected chats as target dicts, or main channel as fallback."""
    chats = await ConnectedChatService.list_active(session)
    if chats:
        return [{"name": c.title, "chat_id": c.chat_id} for c in chats]
    return [{"name": "Main Channel", "chat_id": settings.bot.main_channel_id}]


@router.callback_query(F.data.startswith("item_br:"))
async def on_broadcast_start(
    query: CallbackQuery, bot_user: BotUser, state: FSMContext, session: AsyncSession
):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        await query.answer()
        return
    item_id = query.data.split(":")[1]
    targets = await _get_targets(session)
    all_ids = [t["chat_id"] for t in targets]
    await state.update_data(br_item_id=item_id, br_targets=targets, br_selected=all_ids)
    kb = build_target_selector(item_id, targets, all_ids)
    await query.message.edit_text("📡 Select broadcast targets:", reply_markup=kb)
    await query.answer()


@router.callback_query(BroadcastToggle.filter())
async def on_target_toggle(
    query: CallbackQuery, callback_data: BroadcastToggle, state: FSMContext
):
    data = await state.get_data()
    item_id = data["br_item_id"]
    targets = data["br_targets"]
    selected = list(data["br_selected"])
    chat_id = int(callback_data.chat_id)
    if chat_id in selected:
        selected.remove(chat_id)
    else:
        selected.append(chat_id)
    await state.update_data(br_selected=selected)
    await query.message.edit_reply_markup(
        reply_markup=build_target_selector(item_id, targets, selected)
    )
    await query.answer()


@router.callback_query(BroadcastDone.filter())
async def on_broadcast_confirm(
    query: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot
):
    data = await state.get_data()
    item_id = uuid.UUID(data["br_item_id"])
    selected: list = data["br_selected"]

    if not selected:
        await query.answer("Select at least one target.", show_alert=True)
        return

    from sqlalchemy import select
    result = await session.execute(select(ContentItem).where(ContentItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        await query.answer(INVALID_ACTION, show_alert=True)
        return

    persona = await PersonaService.get_active(session)
    sep = "─" * 28
    header = f"{item.subject}\n{sep}\n" if item.subject else ""
    text = PersonaService.apply_to_text(header + (item.text or ""), persona)

    sent = 0
    for chat_id in selected:
        log = BroadcastLog(
            content_id=item_id,
            target_chat_id=chat_id,
            status=BroadcastStatus.PENDING,
        )
        session.add(log)
        try:
            msg = await bot.send_message(chat_id, text)
            log.status = BroadcastStatus.SENT
            log.message_id = msg.message_id
            sent += 1
        except Exception as exc:
            log.status = BroadcastStatus.FAILED
            log.error_detail = str(exc)[:200]

    await session.commit()
    await state.clear()

    summary = (
        BROADCAST_SENT.format(count=sent, persona=persona.name)
        if persona
        else BROADCAST_NO_PERSONA.format(count=sent)
    )
    await query.message.edit_text(summary, reply_markup=build_menu_row())
    await query.answer()
