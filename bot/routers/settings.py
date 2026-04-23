"bot/routers/settings.py"

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.models.bot_user import BotUser, UserRole

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    
    await message.answer("⚙️ **Settings Panel**\n\n- Timezone: Africa/Lagos\n- AI: Enabled\n- Storage: Active")
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
