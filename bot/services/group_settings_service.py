from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.group_settings import GroupSettings
from bot.models.user_warning import UserWarning
class GroupSettingsService:
    @staticmethod
    async def get(session: AsyncSession, chat_id: int) -> Optional[GroupSettings]:
        result = await session.execute(
            select(GroupSettings).where(GroupSettings.chat_id == chat_id)
        )
        return result.scalar_one_or_none()
    @staticmethod
    async def get_or_default(session: AsyncSession, chat_id: int) -> GroupSettings:
        gs = await GroupSettingsService.get(session, chat_id)
        if not gs:
            gs = GroupSettings(chat_id=chat_id)
        return gs
    @staticmethod
    async def upsert(session: AsyncSession, chat_id: int, **kwargs) -> GroupSettings:
        gs = await GroupSettingsService.get(session, chat_id)
        if not gs:
            gs = GroupSettings(chat_id=chat_id)
            session.add(gs)
        for k, v in kwargs.items():
            setattr(gs, k, v)
        gs.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return gs
class WarnService:
    @staticmethod
    async def get(session: AsyncSession, chat_id: int, user_id: int) -> Optional[UserWarning]:
        result = await session.execute(
            select(UserWarning).where(
                UserWarning.chat_id == chat_id,
                UserWarning.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
    @staticmethod
    async def add(
        session: AsyncSession, chat_id: int, user_id: int, reason: str
    ) -> int:
        """Increment warn count and return new count."""
        row = await WarnService.get(session, chat_id, user_id)
        if not row:
            row = UserWarning(chat_id=chat_id, user_id=user_id, warn_count=0)
            session.add(row)
        row.warn_count    += 1
        row.last_reason    = reason[:256] if reason else None
        row.last_warned_at = datetime.now(timezone.utc)
        await session.commit()
        return row.warn_count
    @staticmethod
    async def reset(session: AsyncSession, chat_id: int, user_id: int) -> None:
        row = await WarnService.get(session, chat_id, user_id)
        if row:
            row.warn_count  = 0
            row.last_reason = None
            await session.commit()
    @staticmethod
    async def count(session: AsyncSession, chat_id: int, user_id: int) -> int:
        row = await WarnService.get(session, chat_id, user_id)
        return row.warn_count if row else 0
