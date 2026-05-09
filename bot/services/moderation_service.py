from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.models.moderation_event import ModerationEvent, ModerationEventType
from bot.utils.spam_keywords import check_spam_regex
from bot.keyboards.moderation_kb import build_moderation_actions
class ModerationService:
    @staticmethod
    async def handle_message(bot: Bot, message: Message, session: AsyncSession):
        text = message.text or message.caption
        if not text:
            return
        is_spam = check_spam_regex(text)
        confidence = 0.5 if is_spam else 0.0
        if is_spam and confidence > 0.85:
            try:
                await message.delete()
            except Exception:
                pass
            event = ModerationEvent(
                event_type=ModerationEventType.SPAM,
                actor_user_id=message.from_user.id,
                chat_id=message.chat.id,
                message_id=message.message_id,
                detail={"text": text, "confidence": confidence, "auto_deleted": True}
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            await ModerationService.send_escalation(bot, event)
    @staticmethod
    async def send_escalation(bot: Bot, event: ModerationEvent):
        kb = build_moderation_actions(str(event.id))
        await bot.send_message(
            settings.bot.owner_id,
            f" **Moderation Escalation**\n\nEvent: {event.event_type.value}\nUser: {event.actor_user_id}\nDetail: {event.detail.get('text', '')[:100]}...",
            reply_markup=kb
        )
