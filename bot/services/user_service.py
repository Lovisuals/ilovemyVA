from datetime import datetime, timezone
from typing import List, Tuple, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole


class UserService:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[BotUser]:
        result = await session.execute(select(BotUser).where(BotUser.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_page(session: AsyncSession, page: int, size: int) -> Tuple[List[BotUser], int]:
        total = await session.scalar(select(func.count()).select_from(BotUser))
        stmt = select(BotUser).offset((page - 1) * size).limit(size).order_by(BotUser.joined_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_all_superadmins(session: AsyncSession) -> List[BotUser]:
        result = await session.execute(
            select(BotUser).where(
                BotUser.role == UserRole.SUPERADMIN,
                BotUser.is_active == True,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def promote(session: AsyncSession, user_id: int, actor_id: int) -> None:
        await session.execute(
            update(BotUser).where(BotUser.id == user_id).values(
                role=UserRole.ADMIN, promoted_by=actor_id
            )
        )
        await session.commit()

    @staticmethod
    async def promote_to_superadmin(session: AsyncSession, user_id: int, actor_id: int) -> None:
        await session.execute(
            update(BotUser).where(BotUser.id == user_id).values(
                role=UserRole.SUPERADMIN, promoted_by=actor_id
            )
        )
        await session.commit()

    @staticmethod
    async def demote(session: AsyncSession, user_id: int) -> None:
        await session.execute(
            update(BotUser).where(BotUser.id == user_id).values(role=UserRole.USER)
        )
        await session.commit()

    @staticmethod
    async def demote_to_admin(session: AsyncSession, user_id: int) -> None:
        await session.execute(
            update(BotUser).where(BotUser.id == user_id).values(role=UserRole.ADMIN)
        )
        await session.commit()

    @staticmethod
    async def deactivate(session: AsyncSession, user_id: int) -> None:
        await session.execute(
            update(BotUser).where(BotUser.id == user_id).values(is_active=False)
        )
        await session.commit()

    @staticmethod
    async def set_verification_code(session: AsyncSession, user_id: int, code: str) -> None:
        await session.execute(
            update(BotUser).where(BotUser.id == user_id).values(
                verification_code=code,
                code_generated_at=datetime.now(timezone.utc),
                code_used=False,
            )
        )
        await session.commit()
