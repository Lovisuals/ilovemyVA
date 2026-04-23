import secrets
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole
from bot.services.user_service import UserService
from bot.strings import WELCOME_SUPERADMIN, WELCOME_ADMIN, WELCOME_USER, WELCOME_GUEST, CODE_ACCEPTED, INVALID_CODE

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, bot_user: BotUser):
    if bot_user.role == UserRole.SUPERADMIN:
        await message.answer(WELCOME_SUPERADMIN)
    elif bot_user.role == UserRole.ADMIN:
        await message.answer(WELCOME_ADMIN)
    elif bot_user.role == UserRole.USER:
        await message.answer(WELCOME_USER)
    else:
        await message.answer(WELCOME_GUEST)

@router.message(F.text.regexp(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$"))
async def on_code_received(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role != UserRole.PENDING:
        return
    code = message.text.upper()
    if bot_user.verification_code == code:
        bot_user.role = UserRole.USER
        bot_user.code_used = True
        await session.commit()
        await message.answer(CODE_ACCEPTED)
    else:
        await message.answer(INVALID_CODE)

@router.message(Command("invite"))
async def cmd_invite(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    code = f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
    await message.answer(f"🎫 **New Invitation Code:**\n\n`{code}`\n\nShare this with a new user.")
