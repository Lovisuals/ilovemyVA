from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import NavData
from bot.config import settings
from bot.keyboards.menu_kb import MENU_BTN, build_menu_row
from bot.models.bot_user import BotUser, UserRole
from bot.models.welcome_config import WelcomeConfig
from bot.states.feature_states import WelcomeSetup
from bot.strings import (
    WELCOME_CURRENT, WELCOME_DISABLED, WELCOME_ENABLED,
    WELCOME_ENTER_MESSAGE, WELCOME_NONE_SET, WELCOME_SAVED,
)

router = Router()


async def _get_config(session: AsyncSession, chat_id: int):
    result = await session.execute(
        select(WelcomeConfig).where(WelcomeConfig.chat_id == chat_id)
    )
    return result.scalar_one_or_none()


@router.callback_query(NavData.filter(F.section == "welcome"))
async def nav_welcome(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    config = await _get_config(session, settings.bot.main_channel_id)
    builder = InlineKeyboardBuilder()
    if config:
        builder.button(
            text="✏️ Edit Message",
            callback_data=NavData(section="welcome_edit").pack(),
        )
        label = "⏸ Disable" if config.is_active else "▶️ Enable"
        builder.button(
            text=label,
            callback_data=NavData(section="welcome_toggle").pack(),
        )
        builder.adjust(2)
        builder.row(MENU_BTN)
        status = "Active ✅" if config.is_active else "Paused ⏸"
        preview = config.message[:150] + ("…" if len(config.message) > 150 else "")
        text = WELCOME_CURRENT.format(status=status, preview=preview)
    else:
        builder.button(
            text="➕ Set Welcome Message",
            callback_data=NavData(section="welcome_edit").pack(),
        )
        builder.row(MENU_BTN)
        text = WELCOME_NONE_SET
    try:
        await query.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass
    await query.answer()


@router.callback_query(NavData.filter(F.section == "welcome_edit"))
async def welcome_edit_start(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await state.set_state(WelcomeSetup.ENTERING_MESSAGE)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Cancel", callback_data=NavData(section="welcome").pack())
    await query.message.edit_text(WELCOME_ENTER_MESSAGE, reply_markup=builder.as_markup())
    await query.answer()


@router.message(WelcomeSetup.ENTERING_MESSAGE)
async def welcome_message_received(
    message: Message, bot_user: BotUser, state: FSMContext, session: AsyncSession
):
    await state.clear()
    config = await _get_config(session, settings.bot.main_channel_id)
    if config:
        config.message = message.text
        config.is_active = True
        config.created_by = bot_user.id
    else:
        session.add(WelcomeConfig(
            chat_id=settings.bot.main_channel_id,
            message=message.text,
            is_active=True,
            created_by=bot_user.id,
        ))
    await session.commit()
    await message.answer(WELCOME_SAVED, reply_markup=build_menu_row())


@router.callback_query(NavData.filter(F.section == "welcome_toggle"))
async def welcome_toggle(query: CallbackQuery, session: AsyncSession):
    config = await _get_config(session, settings.bot.main_channel_id)
    if config:
        config.is_active = not config.is_active
        await session.commit()
        text = WELCOME_ENABLED if config.is_active else WELCOME_DISABLED
        await query.answer(text, show_alert=True)
    await query.answer()


@router.chat_member(F.new_chat_member.status.in_({"member"}))
async def on_new_member(update: ChatMemberUpdated, bot: Bot, session: AsyncSession):
    config = await _get_config(session, update.chat.id)
    if not config or not config.is_active:
        return
    user = update.new_chat_member.user
    name = user.full_name
    username = f"@{user.username}" if user.username else name
    text = config.message.replace("{name}", name).replace("{username}", username).replace("{chat}", update.chat.title or "")
    try:
        await bot.send_message(update.chat.id, text)
    except Exception:
        pass
