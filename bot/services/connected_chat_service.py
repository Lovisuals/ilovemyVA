from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.connected_chat import ConnectedChat


class ConnectedChatService:

    @staticmethod
    async def upsert(
        session: AsyncSession,
        chat_id: int,
        title: str,
        username: Optional[str],
        chat_type: str,
        bot_status: str,
    ) -> ConnectedChat:
        stmt = (
            pg_insert(ConnectedChat)
            .values(
                chat_id=chat_id,
                title=title,
                username=username,
                chat_type=chat_type,
                bot_status=bot_status,
                is_broadcast_target=True,
                added_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_update(
                index_elements=["chat_id"],
                set_=dict(
                    title=title,
                    username=username,
                    bot_status=bot_status,
                    is_broadcast_target=True,
                ),
            )
        )
        await session.execute(stmt)
        await session.commit()
        result = await session.execute(
            select(ConnectedChat).where(ConnectedChat.chat_id == chat_id)
        )
        return result.scalar_one()

    @staticmethod
    async def mark_left(session: AsyncSession, chat_id: int) -> None:
        await session.execute(
            update(ConnectedChat)
            .where(ConnectedChat.chat_id == chat_id)
            .values(bot_status="left", is_broadcast_target=False)
        )
        await session.commit()

    @staticmethod
    async def list_active(session: AsyncSession) -> List[ConnectedChat]:
        result = await session.execute(
            select(ConnectedChat)
            .where(ConnectedChat.bot_status.in_(["member", "administrator"]))
            .order_by(ConnectedChat.title)
        )
        return list(result.scalars().all())

    @staticmethod
    async def toggle_target(session: AsyncSession, chat_id: int) -> bool:
        result = await session.execute(
            select(ConnectedChat).where(ConnectedChat.chat_id == chat_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            return False
        chat.is_broadcast_target = not chat.is_broadcast_target
        await session.commit()
        return chat.is_broadcast_target

    @staticmethod
    async def touch(session: AsyncSession, chat_id: int) -> None:
        await session.execute(
            update(ConnectedChat)
            .where(ConnectedChat.chat_id == chat_id)
            .values(last_active_at=datetime.now(timezone.utc))
        )
        await session.commit()
