"bot/scheduler/jobs.py"

import uuid
import asyncio
from datetime import datetime, timezone
from aiogram import Bot
from bot.config import settings
from bot.models.content_item import ContentItem, ContentBucket
from bot.services.bucket_service import BucketService
from bot.services.broadcast_service import BroadcastService
from bot.strings import MEDICAL_DISCLAIMER, PUBLISH_FAILED_MAX_RETRIES
from database.session import async_session

async def publish_job(item_id: uuid.UUID):
    bot = Bot(token=settings.bot.token)
    
    async with async_session() as session:
        item = await BucketService.get_by_id(session, item_id)
        if not item or item.bucket != ContentBucket.SCHEDULED:
            await bot.session.close()
            return

        # Disclaimer
        if not item.disclaimer_appended:
            item.text = (item.text or "") + f"\n\n{MEDICAL_DISCLAIMER}"
            item.disclaimer_appended = True
            await session.commit()

        # Mock target - in prod this would be a config list
        target_chat_id = settings.bot.storage_channel_id # Using storage for test delivery

        success = False
        for attempt in range(3):
            try:
                await BroadcastService.send(bot, session, item, target_chat_id, "Main Delivery")
                success = True
                break
            except Exception:
                await asyncio.sleep(60 * (attempt + 1))

        if success:
            item.bucket = ContentBucket.PUBLISHED
            item.published_at = datetime.now(timezone.utc)
        else:
            await bot.send_message(
                settings.bot.owner_id,
                PUBLISH_FAILED_MAX_RETRIES.format(id=str(item.id))
            )

        await session.commit()
    
    await bot.session.close()
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
