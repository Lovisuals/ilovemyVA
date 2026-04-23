import logging
from aiogram import Bot
from sqlalchemy import select
from database.session import async_session
from bot.models.content_item import ContentItem, ContentBucket

async def publish_content_job(item_id: str, bot: Bot):
    async with async_session() as session:
        stmt = select(ContentItem).where(ContentItem.id == item_id)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            return
        try:
            await bot.send_message(
                chat_id=item.created_by,
                text=f"🚀 **Scheduled Post Publishing:**\n\n{item.text}"
            )
            item.bucket = ContentBucket.PUBLISHED
            await session.commit()
        except Exception as e:
            logging.error(f"Failed to publish {item_id}: {e}")
