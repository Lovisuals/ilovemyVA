from typing import List, Tuple, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole

class UserService:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[BotUser]:
        stmt = select(BotUser).where(BotUser.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_page(session: AsyncSession, page: int, size: int) -> Tuple[List[BotUser], int]:
        total_stmt = select(func.count()).select_from(BotUser)
        total = await session.scalar(total_stmt)
        stmt = select(BotUser).offset((page - 1) * size).limit(size).order_by(BotUser.joined_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def promote(session: AsyncSession, user_id: int, actor_id: int):
        stmt = update(BotUser).where(BotUser.id == user_id).values(role=UserRole.ADMIN, promoted_by=actor_id)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def demote(session: AsyncSession, user_id: int):
        stmt = update(BotUser).where(BotUser.id == user_id).values(role=UserRole.USER)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def deactivate(session: AsyncSession, user_id: int):
        stmt = update(BotUser).where(BotUser.id == user_id).values(is_active=False)
        await session.execute(stmt)
        await session.commit()
