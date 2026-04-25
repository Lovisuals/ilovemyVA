from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.rate_limit import RateLimitEvent
from bot.strings import RATE_LIMITED

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id

        if not user_id:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        try:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(minutes=1)

            stmt = select(RateLimitEvent).where(
                RateLimitEvent.user_id == user_id,
                RateLimitEvent.window_start > window_start
            )
            result = await session.execute(stmt)
            limit_event = result.scalar_one_or_none()

            if limit_event:
                if limit_event.count >= 30:
                    if event.message:
                        await event.message.answer(RATE_LIMITED)
                    elif event.callback_query:
                        await event.callback_query.answer(RATE_LIMITED, show_alert=True)
                    return
                limit_event.count += 1
            else:
                limit_event = RateLimitEvent(
                    user_id=user_id,
                    window_start=now,
                    count=1
                )
                session.add(limit_event)

            await session.commit()
        except Exception as e:
            # SIDE EFFECT: logs to debug stream. Why necessary: identifies silent DB connection issues affecting rate limiting.
            logger.debug("RATELIMIT-DB-ERR user_id=%s: %s", user_id, e)

        return await handler(event, data)

async def purge_rate_limits(session: AsyncSession):
    threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
    stmt = delete(RateLimitEvent).where(RateLimitEvent.window_start < threshold)
    await session.execute(stmt)
    await session.commit()
