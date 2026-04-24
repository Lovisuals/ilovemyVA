import json
import logging
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy import select
from database.session import async_session
from bot.config import settings
from bot.models.broadcast_log import BroadcastLog, BroadcastStatus
from bot.models.content_item import ContentBucket, ContentItem

logger = logging.getLogger(__name__)


async def publish_content_job(item_id: str) -> None:
    bot = Bot(token=settings.bot.token)
    try:
        async with async_session() as session:
            result = await session.execute(
                select(ContentItem).where(ContentItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                logger.warning("publish_content_job: item %s not found", item_id)
                return

            target_ids: list[int] = []
            if item.target_chat_ids:
                try:
                    target_ids = json.loads(item.target_chat_ids)
                except Exception:
                    pass
            if not target_ids:
                target_ids = [settings.bot.main_channel_id]

            sep = "─" * 28
            header = f"{item.subject}\n{sep}\n" if item.subject else ""
            text = header + (item.text or "")

            try:
                from bot.services.persona_service import PersonaService
                async with async_session() as psession:
                    persona = await PersonaService.get_active(psession)
                    text = PersonaService.apply_to_text(text, persona)
            except Exception as exc:
                logger.warning("publish_content_job: persona fetch failed: %s", exc)

            sent = 0
            for chat_id in target_ids:
                log = BroadcastLog(
                    content_id=item.id,
                    target_chat_id=chat_id,
                    status=BroadcastStatus.PENDING,
                )
                session.add(log)
                try:
                    msg = await bot.send_message(chat_id, text)
                    log.status = BroadcastStatus.SENT
                    log.message_id = msg.message_id
                    log.sent_at = datetime.now(timezone.utc)
                    sent += 1
                except Exception as exc:
                    log.status = BroadcastStatus.FAILED
                    log.error_detail = str(exc)[:200]
                    logger.warning("publish_content_job: failed to send to %s: %s", chat_id, exc)

            item.bucket = ContentBucket.PUBLISHED
            item.published_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info("publish_content_job: item %s sent to %d/%d targets", item_id, sent, len(target_ids))
    finally:
        await bot.session.close()
