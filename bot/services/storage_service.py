"bot/services/storage_service.py"

import uuid
from typing import List, Tuple, Optional

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.storage_record import StorageRecord, FileType

class TelegramStorageService:
    @staticmethod
    async def upload(
        bot: Bot, 
        session: AsyncSession,
        message: Message, 
        uploader_id: int, 
        content_item_id: Optional[uuid.UUID] = None
    ) -> StorageRecord:
        # SIDE EFFECT: Forwarding content to a private storage channel for cloud archiving.
        # Required because Railway trial filesystem is ephemeral.
        forwarded = await message.forward(chat_id=settings.bot.storage_channel_id)
        
        file_id = ""
        file_unique_id = ""
        file_type = FileType.DOCUMENT
        file_size = 0
        
        if message.photo:
            file_id = message.photo[-1].file_id
            file_unique_id = message.photo[-1].file_unique_id
            file_type = FileType.PHOTO
            file_size = message.photo[-1].file_size
        elif message.video:
            file_id = message.video.file_id
            file_unique_id = message.video.file_unique_id
            file_type = FileType.VIDEO
            file_size = message.video.file_size
        elif message.document:
            file_id = message.document.file_id
            file_unique_id = message.document.file_unique_id
            file_type = FileType.DOCUMENT
            file_size = message.document.file_size
            
        record = StorageRecord(
            original_filename=message.document.file_name if message.document else None,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            file_size=file_size,
            storage_message_id=forwarded.message_id,
            storage_channel_id=settings.bot.storage_channel_id,
            uploaded_by=uploader_id,
            content_item_id=content_item_id
        )
        
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def get_file_id(session: AsyncSession, file_unique_id: str) -> Optional[str]:
        stmt = select(StorageRecord.file_id).where(StorageRecord.file_unique_id == file_unique_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(bot: Bot, session: AsyncSession, record_id: uuid.UUID) -> None:
        stmt = select(StorageRecord).where(StorageRecord.id == record_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            # SIDE EFFECT: Deleting archived content from Telegram backend.
            # Maintenance requirement: fulfill owner's right to erase data.
            try:
                await bot.delete_message(record.storage_channel_id, record.storage_message_id)
            except Exception:
                pass
            
            await session.delete(record)
            await session.commit()

    @staticmethod
    async def list_by_uploader(
        session: AsyncSession, 
        uploader_id: int, 
        page: int, 
        per_page: int
    ) -> Tuple[List[StorageRecord], int]:
        stmt_count = select(func.count()).select_from(StorageRecord).where(StorageRecord.uploaded_by == uploader_id)
        count_result = await session.execute(stmt_count)
        total_count = count_result.scalar() or 0
        
        offset = (page - 1) * per_page
        stmt = select(StorageRecord).where(StorageRecord.uploaded_by == uploader_id).offset(offset).limit(per_page)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total_count
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
