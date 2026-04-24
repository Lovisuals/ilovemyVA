from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.bot_user import BotUser, UserRole
from bot.strings import ACCOUNT_DEACTIVATED, PENDING_ACCESS

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        user_id: Optional[int] = None
        user_name: Optional[str] = None
        full_name: Optional[str] = None

        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
            user_name = event.message.from_user.username
            full_name = event.message.from_user.full_name
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            user_name = event.callback_query.from_user.username
            full_name = event.callback_query.from_user.full_name
        elif event.inline_query:
            user_id = event.inline_query.from_user.id
            user_name = event.inline_query.from_user.username
            full_name = event.inline_query.from_user.full_name

        if not user_id:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        try:
            stmt = select(BotUser).where(BotUser.id == user_id)
            result = await session.execute(stmt)
            bot_user = result.scalar_one_or_none()

            is_new_user = False
            if not bot_user:
                is_new_user = True
                role = UserRole.SUPERADMIN if user_id == settings.bot.owner_id else UserRole.PENDING
                bot_user = BotUser(
                    id=user_id,
                    username=user_name,
                    full_name=full_name or "Unknown",
                    role=role,
                    last_seen=datetime.now(timezone.utc)
                )
                session.add(bot_user)
                await session.commit()
                await session.refresh(bot_user)
            else:
                bot_user.last_seen = datetime.now(timezone.utc)
                bot_user.username = user_name
                bot_user.full_name = full_name or bot_user.full_name
                await session.commit()
        except Exception:
            return await handler(event, data)

        if not bot_user.is_active:
            if event.message:
                await event.message.answer(ACCOUNT_DEACTIVATED)
            elif event.callback_query:
                await event.callback_query.answer(ACCOUNT_DEACTIVATED, show_alert=True)
            return

        if bot_user.role == UserRole.PENDING:
            is_start = event.message and event.message.text and event.message.text.startswith("/start")
            is_code = event.message and event.message.text and "-" in event.message.text
            if not (is_start or is_code):
                if event.message:
                    await event.message.answer(PENDING_ACCESS)
                elif event.callback_query:
                    await event.callback_query.answer(PENDING_ACCESS, show_alert=True)
                return

        data["bot_user"] = bot_user
        data["is_new_user"] = is_new_user

        return await handler(event, data)
