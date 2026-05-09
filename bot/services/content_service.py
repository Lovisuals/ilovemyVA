import uuid
from typing import List, Tuple, Optional
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.content_item import ContentItem, ContentBucket
class ContentService:
    @staticmethod
    async def create_item(session: AsyncSession, **kwargs) -> ContentItem:
        item = ContentItem(**kwargs)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
    @staticmethod
    async def get_by_id(session: AsyncSession, item_id: uuid.UUID) -> Optional[ContentItem]:
        stmt = select(ContentItem).where(ContentItem.id == item_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    @staticmethod
    async def get_page(session: AsyncSession, bucket: ContentBucket, page: int, size: int) -> Tuple[List[ContentItem], int]:
        total_stmt = select(func.count()).select_from(ContentItem).where(ContentItem.bucket == bucket)
        total = await session.scalar(total_stmt)
        stmt = select(ContentItem).where(ContentItem.bucket == bucket).offset((page - 1) * size).limit(size).order_by(ContentItem.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all()), total
    @staticmethod
    async def update_item(session: AsyncSession, item_id: uuid.UUID, **kwargs):
        stmt = update(ContentItem).where(ContentItem.id == item_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
    @staticmethod
    async def delete_item(session: AsyncSession, item_id: uuid.UUID):
        stmt = delete(ContentItem).where(ContentItem.id == item_id)
        await session.execute(stmt)
        await session.commit()
