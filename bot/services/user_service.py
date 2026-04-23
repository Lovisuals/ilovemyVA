"bot/services/user_service.py"

from typing import List, Tuple, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole

class UserService:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[BotUser]:
        stmt = select(BotUser).where(BotUser.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_page(session: AsyncSession, page: int, per_page: int) -> Tuple[List[BotUser], int]:
        stmt_count = select(func.count()).select_from(BotUser)
        count_result = await session.execute(stmt_count)
        total_count = count_result.scalar() or 0

        offset = (page - 1) * per_page
        stmt = select(BotUser).order_by(BotUser.joined_at.desc().nulls_last()).offset(offset).limit(per_page)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total_count

    @staticmethod
    async def promote(session: AsyncSession, user_id: int, actor_id: int) -> BotUser:
        user = await UserService.get_by_id(session, user_id)
        if not user:
            raise ValueError("User not found")
        if user.role != UserRole.USER:
            raise ValueError("Only regular users can be promoted")

        user.role = UserRole.ADMIN
        user.promoted_by = actor_id
        try:
            await session.commit()
            await session.refresh(user)
            return user
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def demote(session: AsyncSession, user_id: int) -> BotUser:
        user = await UserService.get_by_id(session, user_id)
        if not user:
            raise ValueError("User not found")
        if user.role == UserRole.SUPERADMIN:
            raise ValueError("Cannot demote superadmin")

        user.role = UserRole.USER
        try:
            await session.commit()
            await session.refresh(user)
            return user
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def deactivate(session: AsyncSession, user_id: int) -> BotUser:
        user = await UserService.get_by_id(session, user_id)
        if not user:
            raise ValueError("User not found")
        if user.role == UserRole.SUPERADMIN:
            raise ValueError("Cannot deactivate superadmin")

        user.is_active = False
        try:
            await session.commit()
            await session.refresh(user)
            return user
        except Exception:
            await session.rollback()
            raise
