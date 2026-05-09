"""
bot/services/content_service.py

All read/write operations are scoped to a tenant_id.
Pass tenant_id=0 only for legacy/admin contexts where cross-tenant reads
are explicitly intentional (e.g., scheduler job recovery at startup).
"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.content_item import ContentBucket, ContentItem


class ContentService:

    @staticmethod
    async def create_item(
        session: AsyncSession,
        tenant_id: int,
        **kwargs,
    ) -> ContentItem:
        """Create a new ContentItem scoped to tenant_id."""
        item = ContentItem(tenant_id=tenant_id, **kwargs)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        item_id: uuid.UUID,
        tenant_id: Optional[int] = None,
    ) -> Optional[ContentItem]:
        """
        Fetch a single item by UUID.
        If tenant_id is provided, enforce ownership — returns None if mismatch.
        Pass tenant_id=None only from the scheduler job (reads by item_id directly).
        """
        stmt = select(ContentItem).where(ContentItem.id == item_id)
        if tenant_id is not None:
            stmt = stmt.where(ContentItem.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_page(
        session: AsyncSession,
        bucket: ContentBucket,
        page: int,
        size: int,
        tenant_id: int,
    ) -> Tuple[List[ContentItem], int]:
        """Paginated list scoped to tenant + bucket."""
        total_stmt = select(func.count()).select_from(ContentItem).where(
            ContentItem.bucket == bucket,
            ContentItem.tenant_id == tenant_id,
        )
        total = await session.scalar(total_stmt)
        stmt = (
            select(ContentItem)
            .where(
                ContentItem.bucket == bucket,
                ContentItem.tenant_id == tenant_id,
            )
            .order_by(ContentItem.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all()), (total or 0)

    @staticmethod
    async def update_item(
        session: AsyncSession,
        item_id: uuid.UUID,
        tenant_id: int,
        **kwargs,
    ) -> None:
        """Update fields on a ContentItem; enforces tenant ownership."""
        stmt = (
            update(ContentItem)
            .where(
                ContentItem.id == item_id,
                ContentItem.tenant_id == tenant_id,
            )
            .values(**kwargs)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def delete_item(
        session: AsyncSession,
        item_id: uuid.UUID,
        tenant_id: int,
    ) -> None:
        """Delete a ContentItem; enforces tenant ownership."""
        stmt = delete(ContentItem).where(
            ContentItem.id == item_id,
            ContentItem.tenant_id == tenant_id,
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def count_published_this_month(
        session: AsyncSession,
        tenant_id: int,
    ) -> int:
        """Count posts published in the current calendar month (quota check)."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count()).select_from(ContentItem).where(
            ContentItem.tenant_id == tenant_id,
            ContentItem.bucket == ContentBucket.PUBLISHED,
            ContentItem.published_at >= month_start,
        )
        result = await session.scalar(stmt)
        return result or 0
