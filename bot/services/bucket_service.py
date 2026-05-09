"""
bot/services/bucket_service.py

Thin wrapper around ContentService for bucket-specific operations.
All queries are tenant-scoped.  tenant_id is mandatory on every method.
"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.content_item import ContentBucket, ContentItem
from bot.services.content_service import ContentService
from bot.utils.hashing import calculate_content_hash


class BucketService:

    @staticmethod
    async def get_page(
        session: AsyncSession,
        bucket: ContentBucket,
        page: int,
        per_page: int,
        tenant_id: int,
    ) -> Tuple[List[ContentItem], int]:
        """Paginated bucket view — tenant-scoped."""
        return await ContentService.get_page(
            session, bucket, page, per_page, tenant_id=tenant_id
        )

    @staticmethod
    async def create_draft(
        session: AsyncSession,
        text: Optional[str],
        file_ids: List[dict],
        created_by: int,
        tenant_id: int,
        media_group_id: Optional[str] = None,
    ) -> ContentItem:
        """Create a DRAFTS item with content hash for dedup."""
        content_hash = calculate_content_hash(text or "", file_ids)
        return await ContentService.create_item(
            session,
            tenant_id=tenant_id,
            bucket=ContentBucket.DRAFTS,
            text=text,
            file_ids=file_ids,
            media_group_id=media_group_id,
            content_hash=content_hash,
            created_by=created_by,
        )

    @staticmethod
    async def move_bucket(
        session: AsyncSession,
        item_id: uuid.UUID,
        target_bucket: ContentBucket,
        tenant_id: int,
    ) -> ContentItem:
        """Move an item to a different bucket; enforces tenant ownership."""
        stmt = select(ContentItem).where(
            ContentItem.id == item_id,
            ContentItem.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError(f"Item {item_id} not found for tenant {tenant_id}")
        item.bucket = target_bucket
        try:
            await session.commit()
            await session.refresh(item)
            return item
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def delete_item(
        session: AsyncSession,
        item_id: uuid.UUID,
        tenant_id: int,
    ) -> None:
        """Delete an item; enforces tenant ownership."""
        await ContentService.delete_item(session, item_id, tenant_id=tenant_id)

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        item_id: uuid.UUID,
        tenant_id: int,
    ) -> Optional[ContentItem]:
        """Fetch by UUID with tenant enforcement."""
        return await ContentService.get_by_id(session, item_id, tenant_id=tenant_id)
