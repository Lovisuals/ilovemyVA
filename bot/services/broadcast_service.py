"bot/services/broadcast_service.py"

import uuid
from datetime import datetime, timezone, timedelta

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.content_item import ContentItem
from bot.models.broadcast_log import BroadcastLog, BroadcastStatus
from bot.config import settings

class BroadcastError(Exception):
    pass

class BroadcastService:
    @staticmethod
    async def send(
        bot: Bot, 
        session: AsyncSession,
        item: ContentItem, 
        target_chat_id: int, 
        target_name: str,
        force: bool = False
    ) -> BroadcastLog:
        if not force:
            window = datetime.now(timezone.utc) - timedelta(hours=24)
            stmt = select(BroadcastLog).where(
                BroadcastLog.target_chat_id == target_chat_id,
                BroadcastLog.status == BroadcastStatus.SENT,
                BroadcastLog.created_at >= window
            )
            result = await session.execute(stmt)
            existing_logs = result.scalars().all()
            
            for log in existing_logs:
                # Assuming we compare content hashes
                log_stmt = select(ContentItem.content_hash).where(ContentItem.id == log.content_id)
                hash_result = await session.execute(log_stmt)
                old_hash = hash_result.scalar()
                if old_hash == item.content_hash:
                    skipped_log = BroadcastLog(
                        content_id=item.id,
                        target_chat_id=target_chat_id,
                        target_name=target_name,
                        status=BroadcastStatus.SKIPPED_DEDUP
                    )
                    session.add(skipped_log)
                    await session.commit()
                    return skipped_log

        try:
            # SIDE EFFECT: Calls Telegram API to deliver content. 
            # Core business requirement: deliver content to members.
            message_id = None
            if not item.file_ids:
                msg = await bot.send_message(
                    chat_id=target_chat_id,
                    text=item.text or "",
                    parse_mode=item.parse_mode.value
                )
                message_id = msg.message_id
            else:
                # Simplified media handling - first file only for now or media group
                if len(item.file_ids) == 1:
                    file_data = item.file_ids[0]
                    if file_data["type"] == "photo":
                        msg = await bot.send_photo(
                            chat_id=target_chat_id,
                            photo=file_data["file_id"],
                            caption=item.text,
                            parse_mode=item.parse_mode.value
                        )
                        message_id = msg.message_id
                else:
                    from aiogram.types import InputMediaPhoto
                    media = [InputMediaPhoto(media=f["file_id"], caption=item.text if i == 0 else None) for i, f in enumerate(item.file_ids)]
                    msgs = await bot.send_media_group(chat_id=target_chat_id, media=media)
                    message_id = msgs[0].message_id

            log = BroadcastLog(
                content_id=item.id,
                target_chat_id=target_chat_id,
                target_name=target_name,
                message_id=message_id,
                status=BroadcastStatus.SENT,
                sent_at=datetime.now(timezone.utc)
            )
            session.add(log)
            await session.commit()
            return log

        except Exception as e:
            error_log = BroadcastLog(
                content_id=item.id,
                target_chat_id=target_chat_id,
                target_name=target_name,
                status=BroadcastStatus.FAILED,
                error_detail=str(e)
            )
            session.add(error_log)
            await session.commit()
            raise BroadcastError(str(e))
