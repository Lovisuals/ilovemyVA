import uuid
from typing import List, Optional, Tuple

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.storage_record import FileType, StorageRecord


class TelegramStorageService:

    @staticmethod
    async def upload(
        bot: Bot,
        session: AsyncSession,
        message: Message,
        uploader_id: int,
        tenant_id: int,
        content_item_id: Optional[uuid.UUID] = None,
    ) -> StorageRecord:
        copied = await bot.copy_message(
            chat_id=settings.bot.storage_channel_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        file_id        = ""
        file_unique_id = ""
        file_type      = FileType.DOCUMENT
        file_size      = 0

        if message.photo:
            file_id        = message.photo[-1].file_id
            file_unique_id = message.photo[-1].file_unique_id
            file_type      = FileType.PHOTO
            file_size      = message.photo[-1].file_size or 0
        elif message.video:
            file_id        = message.video.file_id
            file_unique_id = message.video.file_unique_id
            file_type      = FileType.VIDEO
            file_size      = message.video.file_size or 0
        elif message.document:
            file_id        = message.document.file_id
            file_unique_id = message.document.file_unique_id
            file_type      = FileType.DOCUMENT
            file_size      = message.document.file_size or 0

        record = StorageRecord(
            tenant_id=tenant_id,
            original_filename=message.document.file_name if message.document else None,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            file_size=file_size,
            storage_message_id=copied.message_id,
            storage_channel_id=settings.bot.storage_channel_id,
            uploaded_by=uploader_id,
            content_item_id=content_item_id,
        )
        session.add(record)
        try:
            await session.commit()
            await session.refresh(record)
            return record
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def get_file_id(session: AsyncSession, file_unique_id: str) -> Optional[str]:
        stmt = select(StorageRecord.file_id).where(
            StorageRecord.file_unique_id == file_unique_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(bot: Bot, session: AsyncSession, record_id: uuid.UUID) -> None:
        stmt   = select(StorageRecord).where(StorageRecord.id == record_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            try:
                await bot.delete_message(record.storage_channel_id, record.storage_message_id)
            except Exception:
                pass
            try:
                await session.delete(record)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    async def list_by_uploader(
        session: AsyncSession,
        uploader_id: int,
        tenant_id: int,
        page: int,
        per_page: int,
    ) -> Tuple[List[StorageRecord], int]:
        base = (
            StorageRecord.uploaded_by == uploader_id,
            StorageRecord.tenant_id == tenant_id,
        )
        count_stmt = select(func.count()).select_from(StorageRecord).where(*base)
        total      = await session.scalar(count_stmt) or 0
        offset     = (page - 1) * per_page
        stmt = (
            select(StorageRecord)
            .where(*base)
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all()), total
