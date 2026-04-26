import secrets
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import OnboardGen
from bot.config import settings
from bot.keyboards.menu_kb import build_main_menu
from bot.keyboards.user_mgmt_kb import build_superadmin_contact_kb
from bot.models.bot_user import BotUser, UserRole
from bot.services.user_service import UserService
from bot.strings import (
    ADMIN_CODE_FOR_USER, CODE_ACCEPTED, CODE_EXPIRED,
    INVALID_CODE, NEW_USER_NOTIFICATION,
    WELCOME_ADMIN, WELCOME_GUEST, WELCOME_PENDING,
    WELCOME_SUPERADMIN, WELCOME_USER,
    MENU_ADMIN, MENU_USER,
)

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, bot_user: BotUser, session: AsyncSession, is_new_user: bool = False):
    
    if bot_user.role == UserRole.SUPERADMIN:
        await message.answer(WELCOME_SUPERADMIN)
        await message.answer(MENU_ADMIN, reply_markup=build_main_menu(bot_user.role))
    elif bot_user.role == UserRole.ADMIN:
        await message.answer(WELCOME_ADMIN)
        await message.answer(MENU_ADMIN, reply_markup=build_main_menu(bot_user.role))
    elif bot_user.role == UserRole.USER:
        await message.answer(WELCOME_USER)
        await message.answer(MENU_USER, reply_markup=build_main_menu(bot_user.role))
    else:
        if bot_user.verification_code:
            await message.answer(WELCOME_GUEST)
        else:
            superadmins = await UserService.get_all_superadmins(session)
            kb = build_superadmin_contact_kb(superadmins)
            await message.answer(WELCOME_PENDING, reply_markup=kb)

        if is_new_user:
            try:
                builder = InlineKeyboardBuilder()
                builder.button(
                    text="Generate Access Code",
                    callback_data=OnboardGen(user_id=bot_user.id).pack(),
                )
                await message.bot.send_message(
                    settings.bot.owner_id,
                    NEW_USER_NOTIFICATION.format(
                        name=bot_user.full_name,
                        username=bot_user.username or "N/A",
                        user_id=bot_user.id,
                    ),
                    reply_markup=builder.as_markup(),
                )
            except Exception:
                pass

@router.message(F.text.regexp(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$"))
async def on_code_received(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role != UserRole.PENDING:
        return
    code = message.text.upper()
    if bot_user.verification_code != code:
        await message.answer(INVALID_CODE)
        return
    if bot_user.code_generated_at and (
        datetime.now(timezone.utc) - bot_user.code_generated_at
    ).total_seconds() > 600:
        await message.answer(CODE_EXPIRED)
        return
    bot_user.role = UserRole.USER
    bot_user.code_used = True
    bot_user.joined_at = datetime.now(timezone.utc)
    await session.commit()
    await message.answer(CODE_ACCEPTED)
    await message.answer(MENU_USER, reply_markup=build_main_menu(UserRole.USER))

@router.callback_query(OnboardGen.filter())
async def on_onboard_gen(
    query: CallbackQuery,
    callback_data: OnboardGen,
    bot_user: BotUser,
    session: AsyncSession,
):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        await query.answer()
        return
    target = await UserService.get_by_id(session, callback_data.user_id)
    if not target or target.role != UserRole.PENDING:
        await query.answer("User already onboarded or not found.", show_alert=True)
        return
    code = f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
    await UserService.set_verification_code(session, target.id, code)
    await query.answer()
    await query.message.edit_text(ADMIN_CODE_FOR_USER.format(code=code))
