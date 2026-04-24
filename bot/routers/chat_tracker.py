"""
Tracks every group and channel the bot is added to or removed from.
Fires on my_chat_member updates (bot's own membership changes).
Fires on channel_post / message to keep last_active_at fresh.
"""
import logging

from aiogram import F, Router
from aiogram.types import ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.connected_chat_service import ConnectedChatService

logger = logging.getLogger(__name__)
router = Router()

_ACTIVE_STATUSES = {"member", "administrator"}
_GONE_STATUSES   = {"left", "kicked", "restricted"}


@router.my_chat_member()
async def on_bot_membership(event: ChatMemberUpdated, session: AsyncSession) -> None:
    status = event.new_chat_member.status
    chat   = event.chat

    if chat.type not in ("group", "supergroup", "channel"):
        return

    try:
        if status in _ACTIVE_STATUSES:
            await ConnectedChatService.upsert(
                session,
                chat_id=chat.id,
                title=chat.title or str(chat.id),
                username=getattr(chat, "username", None),
                chat_type=chat.type,
                bot_status=status,
            )
            logger.info("Bot joined %s (%s) as %s", chat.title, chat.id, status)
        elif status in _GONE_STATUSES:
            await ConnectedChatService.mark_left(session, chat.id)
            logger.info("Bot left/kicked from %s (%s)", chat.title, chat.id)
    except Exception as exc:
        logger.warning("chat_tracker error for %s: %s", chat.id, exc)


@router.channel_post(F.text)
@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def on_chat_activity(message: Message, session: AsyncSession) -> None:
    try:
        await ConnectedChatService.touch(session, message.chat.id)
    except Exception:
        pass
