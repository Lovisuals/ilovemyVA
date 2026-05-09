import uuid
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks import NavData, PersonaAction
from bot.keyboards.menu_kb import MENU_BTN
from bot.keyboards.persona_kb import build_persona_actions, build_persona_list
from bot.models.bot_user import BotUser, UserRole
from bot.services.persona_service import PersonaService
from bot.states.feature_states import PersonaCreation
from bot.strings import (
    PERSONA_ACTIVATED, PERSONA_CREATED, PERSONA_DELETED,
    PERSONA_DETAIL, PERSONA_ENTER_NAME, PERSONA_LIST_HEADER,
)
router = Router()
@router.callback_query(NavData.filter(F.section == "persona"))
async def nav_persona(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    personas = await PersonaService.list_all(session)
    try:
        await query.message.edit_text(PERSONA_LIST_HEADER, reply_markup=build_persona_list(personas))
    except TelegramBadRequest:
        pass
    await query.answer()
@router.callback_query(NavData.filter(F.section == "persona_new"))
async def persona_new_start(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await state.set_state(PersonaCreation.ENTERING_NAME)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Cancel", callback_data=NavData(section="persona").pack())
    await query.message.edit_text(PERSONA_ENTER_NAME, reply_markup=builder.as_markup())
    await query.answer()
@router.message(PersonaCreation.ENTERING_NAME)
async def persona_name_received(
    message: Message, bot_user: BotUser, state: FSMContext, session: AsyncSession
):
    raw = message.text.strip()
    if "|" in raw:
        parts = raw.split("|", 1)
        name = parts[0].strip()
        title = parts[1].strip()
        signature = "— {name} · {title}"
    else:
        name = raw
        title = None
        signature = "— {name}"
    await PersonaService.create(session, name, title, signature, bot_user.id)
    await state.clear()
    personas = await PersonaService.list_all(session)
    await message.answer(
        PERSONA_CREATED.format(name=name),
        reply_markup=build_persona_list(personas),
    )
@router.callback_query(PersonaAction.filter(F.action == "view"))
async def persona_view(
    query: CallbackQuery, callback_data: PersonaAction, session: AsyncSession
):
    persona = await PersonaService.get_by_id(session, uuid.UUID(callback_data.persona_id))
    if not persona:
        await query.answer("Not found.", show_alert=True)
        return
    sig = PersonaService.render_signature(persona)
    text = PERSONA_DETAIL.format(
        name=persona.name,
        title=persona.title or "—",
        signature=sig,
        status="Active " if persona.is_active else "Inactive",
    )
    await query.message.edit_text(
        text, reply_markup=build_persona_actions(callback_data.persona_id, persona.is_active)
    )
    await query.answer()
@router.callback_query(PersonaAction.filter(F.action == "activate"))
async def persona_activate(
    query: CallbackQuery, callback_data: PersonaAction, session: AsyncSession
):
    await PersonaService.activate(session, uuid.UUID(callback_data.persona_id))
    personas = await PersonaService.list_all(session)
    await query.message.edit_text(PERSONA_ACTIVATED, reply_markup=build_persona_list(personas))
    await query.answer()
@router.callback_query(PersonaAction.filter(F.action == "delete"))
async def persona_delete(
    query: CallbackQuery, callback_data: PersonaAction, session: AsyncSession
):
    await PersonaService.delete(session, uuid.UUID(callback_data.persona_id))
    personas = await PersonaService.list_all(session)
    await query.message.edit_text(PERSONA_DELETED, reply_markup=build_persona_list(personas))
    await query.answer()
