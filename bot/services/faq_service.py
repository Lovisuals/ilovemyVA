import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.faq_entry import FaqEntry


class FaqService:
    @staticmethod
    async def list_all(session: AsyncSession) -> List[FaqEntry]:
        result = await session.execute(select(FaqEntry).order_by(FaqEntry.created_at))
        return list(result.scalars().all())

    @staticmethod
    async def list_active(session: AsyncSession) -> List[FaqEntry]:
        result = await session.execute(
            select(FaqEntry).where(FaqEntry.is_active == True).order_by(FaqEntry.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def find_match(session: AsyncSession, text: str) -> Optional[FaqEntry]:
        entries = await FaqService.list_active(session)
        lower = text.lower()
        for entry in entries:
            t = entry.trigger.lower()
            if entry.match_type == "exact" and lower == t:
                return entry
            if entry.match_type == "contains" and t in lower:
                return entry
            if entry.match_type == "startswith" and lower.startswith(t):
                return entry
        return None

    @staticmethod
    async def create(
        session: AsyncSession,
        trigger: str,
        response: str,
        match_type: str,
        created_by: int,
    ) -> FaqEntry:
        entry = FaqEntry(
            trigger=trigger, response=response,
            match_type=match_type, created_by=created_by,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry

    @staticmethod
    async def get_by_id(session: AsyncSession, entry_id: uuid.UUID) -> Optional[FaqEntry]:
        result = await session.execute(select(FaqEntry).where(FaqEntry.id == entry_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def toggle(session: AsyncSession, entry_id: uuid.UUID) -> None:
        entry = await FaqService.get_by_id(session, entry_id)
        if entry:
            entry.is_active = not entry.is_active
            await session.commit()

    @staticmethod
    async def delete(session: AsyncSession, entry_id: uuid.UUID) -> None:
        entry = await FaqService.get_by_id(session, entry_id)
        if entry:
            await session.delete(entry)
            await session.commit()
