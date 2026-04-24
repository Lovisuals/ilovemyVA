from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.menu_kb import build_menu_row
from bot.models.bot_user import BotUser, UserRole
from bot.strings import SETTINGS_TEXT

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    await message.answer(SETTINGS_TEXT, reply_markup=build_menu_row())
