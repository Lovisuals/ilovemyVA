import uuid
from typing import List, Tuple, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.content_item import ContentItem, ContentBucket
from bot.utils.hashing import calculate_content_hash
class BucketService:
    @staticmethod
    async def get_page(
        session: AsyncSession,
        bucket: ContentBucket,
        page: int,
        per_page: int
    ) -> Tuple[List[ContentItem], int]:
        stmt_count = select(func.count()).select_from(ContentItem).where(ContentItem.bucket == bucket)
        count_result = await session.execute(stmt_count)
        total_count = count_result.scalar() or 0
        offset = (page - 1) * per_page
        stmt = select(ContentItem).where(ContentItem.bucket == bucket).order_by(ContentItem.created_at.desc()).offset(offset).limit(per_page)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return list(items), total_count
    @staticmethod
    async def create_draft(
        session: AsyncSession,
        text: Optional[str],
        file_ids: List[dict],
        created_by: int,
        media_group_id: Optional[str] = None
    ) -> ContentItem:
        content_hash = calculate_content_hash(text or "", file_ids)
        item = ContentItem(
            bucket=ContentBucket.DRAFTS,
            text=text,
            file_ids=file_ids,
            media_group_id=media_group_id,
            content_hash=content_hash,
            created_by=created_by
        )
        session.add(item)
        try:
            await session.commit()
            await session.refresh(item)
            return item
        except Exception:
            await session.rollback()
            raise
    @staticmethod
    async def move_bucket(session: AsyncSession, item_id: uuid.UUID, target_bucket: ContentBucket) -> ContentItem:
        stmt = select(ContentItem).where(ContentItem.id == item_id)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError(f"Item {item_id} not found")
        item.bucket = target_bucket
        try:
            await session.commit()
            await session.refresh(item)
            return item
        except Exception:
            await session.rollback()
            raise
    @staticmethod
    async def delete_item(session: AsyncSession, item_id: uuid.UUID) -> None:
        stmt = delete(ContentItem).where(ContentItem.id == item_id)
        try:
            await session.execute(stmt)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    @staticmethod
    async def get_by_id(session: AsyncSession, item_id: uuid.UUID) -> Optional[ContentItem]:
        stmt = select(ContentItem).where(ContentItem.id == item_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
