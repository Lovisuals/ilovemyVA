"bot/routers/onboarding.py"

from datetime import datetime, timezone, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.bot_user import BotUser, UserRole
from bot.utils.luhn import generate_verification_code, validate_luhn
from bot.strings import (
    WELCOME_PENDING, NEW_USER_NOTIFICATION, 
    ADMIN_CODE_FOR_USER, ONBOARD_SUCCESS, 
    CODE_INVALID, CODE_EXPIRED
)

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, bot_user: BotUser, bot: Bot):
    if bot_user.role != UserRole.PENDING:
        await message.answer(f"Hello, {bot_user.full_name}. Use /admin to manage content.")
        return

    await message.answer(WELCOME_PENDING)
    
    # Notify admins
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔑 Generate Code for @{bot_user.username or 'user'}", callback_data=f"onb_g:{bot_user.id}")]
    ])
    
    await bot.send_message(
        settings.bot.owner_id,
        NEW_USER_NOTIFICATION.format(
            name=bot_user.full_name, 
            username=bot_user.username or "N/A", 
            user_id=bot_user.id
        ),
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("onb_g:"))
async def on_generate_code(query: CallbackQuery, session: AsyncSession):
    user_id = int(query.data.split(":")[1])
    code = generate_verification_code(user_id)
    
    stmt = select(BotUser).where(BotUser.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_with_none()
    
    if user:
        user.verification_code = code
        user.code_generated_at = datetime.now(timezone.utc)
        user.code_used = False
        await session.commit()
        
        await query.message.answer(ADMIN_CODE_FOR_USER.format(code=code), parse_mode="Markdown")
        await query.answer("Code generated.")

@router.message(lambda m: m.text and "-" in m.text)
async def on_code_submission(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role != UserRole.PENDING:
        return

    submitted_code = message.text.strip()
    
    if not validate_luhn(submitted_code):
        await message.answer(CODE_INVALID)
        return

    if bot_user.verification_code != submitted_code:
        await message.answer(CODE_INVALID)
        return

    expiry = bot_user.code_generated_at + timedelta(minutes=10)
    if datetime.now(timezone.utc) > expiry:
        await message.answer(CODE_EXPIRED)
        return

    if bot_user.code_used:
        await message.answer(CODE_INVALID)
        return

    bot_user.role = UserRole.USER
    bot_user.code_used = True
    bot_user.joined_at = datetime.now(timezone.utc)
    await session.commit()
    
    await message.answer(ONBOARD_SUCCESS)
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
