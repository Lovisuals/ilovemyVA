import uuid
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks import FaqAction, NavData
from bot.keyboards.faq_kb import build_faq_actions, build_faq_list
from bot.models.bot_user import BotUser, UserRole
from bot.services.faq_service import FaqService
from bot.states.feature_states import FaqCreation
from bot.strings import (
    FAQ_CREATED, FAQ_DELETED, FAQ_DETAIL,
    FAQ_ENTER_RESPONSE, FAQ_ENTER_TRIGGER, FAQ_LIST_HEADER,
)
router = Router()
@router.callback_query(NavData.filter(F.section == "faq"))
async def nav_faq(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    entries = await FaqService.list_all(session)
    try:
        await query.message.edit_text(FAQ_LIST_HEADER, reply_markup=build_faq_list(entries))
    except TelegramBadRequest:
        pass
    await query.answer()
@router.callback_query(NavData.filter(F.section == "faq_new"))
async def faq_new_start(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await state.set_state(FaqCreation.ENTERING_TRIGGER)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Cancel", callback_data=NavData(section="faq").pack())
    await query.message.edit_text(FAQ_ENTER_TRIGGER, reply_markup=builder.as_markup())
    await query.answer()
@router.message(FaqCreation.ENTERING_TRIGGER)
async def faq_trigger_received(message: Message, state: FSMContext):
    await state.update_data(faq_trigger=message.text.strip())
    await state.set_state(FaqCreation.ENTERING_RESPONSE)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Cancel", callback_data=NavData(section="faq").pack())
    await message.answer(FAQ_ENTER_RESPONSE, reply_markup=builder.as_markup())
@router.message(FaqCreation.ENTERING_RESPONSE)
async def faq_response_received(
    message: Message, bot_user: BotUser, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    trigger = data["faq_trigger"]
    await FaqService.create(session, trigger, message.text.strip(), "contains", bot_user.id)
    await state.clear()
    entries = await FaqService.list_all(session)
    await message.answer(FAQ_CREATED.format(trigger=trigger), reply_markup=build_faq_list(entries))
@router.callback_query(FaqAction.filter(F.action == "view"))
async def faq_view(
    query: CallbackQuery, callback_data: FaqAction, session: AsyncSession
):
    entry = await FaqService.get_by_id(session, uuid.UUID(callback_data.entry_id))
    if not entry:
        await query.answer("Not found.", show_alert=True)
        return
    text = FAQ_DETAIL.format(
        trigger=entry.trigger,
        match=entry.match_type,
        response=entry.response[:200],
        status="Active " if entry.is_active else "Paused ⏸",
    )
    await query.message.edit_text(
        text, reply_markup=build_faq_actions(callback_data.entry_id, entry.is_active)
    )
    await query.answer()
@router.callback_query(FaqAction.filter(F.action == "toggle"))
async def faq_toggle(
    query: CallbackQuery, callback_data: FaqAction, session: AsyncSession
):
    await FaqService.toggle(session, uuid.UUID(callback_data.entry_id))
    entries = await FaqService.list_all(session)
    await query.message.edit_text(FAQ_LIST_HEADER, reply_markup=build_faq_list(entries))
    await query.answer()
@router.callback_query(FaqAction.filter(F.action == "delete"))
async def faq_delete(
    query: CallbackQuery, callback_data: FaqAction, session: AsyncSession
):
    await FaqService.delete(session, uuid.UUID(callback_data.entry_id))
    entries = await FaqService.list_all(session)
    await query.message.edit_text(FAQ_DELETED, reply_markup=build_faq_list(entries))
    await query.answer()
@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def auto_reply(message: Message, session: AsyncSession):
    if not message.text:
        return
    entry = await FaqService.find_match(session, message.text)
    if entry:
        await message.reply(entry.response)
