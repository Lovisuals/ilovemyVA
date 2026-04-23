"bot/routers/moderation.py"

import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.models.moderation_event import ModerationEvent, ModerationResolution
from bot.services.moderation_service import ModerationService
from bot.strings import INVALID_ACTION

router = Router()

@router.callback_query(F.data.startswith("mod_r:"))
async def on_moderation_resolve(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    parts = query.data.split(":")
    event_id = uuid.UUID(parts[1])
    resolution_str = parts[2]
    resolution = ModerationResolution(resolution_str)
    
    stmt = select(ModerationEvent).where(ModerationEvent.id == event_id)
    result = await session.execute(stmt)
    event = result.scalar_one_with_none()
    
    if not event:
        await query.answer(INVALID_ACTION)
        return

    event.resolution = resolution
    event.resolved_by = bot_user.id
    await session.commit()
    
    await query.message.edit_text(f"🛡 Event resolved as: **{resolution.value.upper()}** by {bot_user.full_name}")
    await query.answer()

@router.message()
async def on_any_message(message: Message, bot: Bot, session: AsyncSession, bot_user: BotUser):
    # Only moderate regular users in groups/channels
    if bot_user.role == UserRole.USER and message.chat.type in ["group", "supergroup"]:
        await ModerationService.handle_message(bot, message, session)
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
