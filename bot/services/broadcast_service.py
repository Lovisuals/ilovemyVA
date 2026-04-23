import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.broadcast_log import BroadcastLog, BroadcastStatus

class BroadcastService:
    @staticmethod
    async def queue_broadcast(session: AsyncSession, item_id: uuid.UUID, targets: List[int]):
        for target in targets:
            log = BroadcastLog(
                content_id=item_id,
                target_chat_id=target,
                status=BroadcastStatus.PENDING
            )
            session.add(log)
        await session.commit()
