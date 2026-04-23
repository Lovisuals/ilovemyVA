"bot/middlewares/error_handler.py"

import traceback
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Update

from bot.config import settings
from bot.models.audit_log import AuditLog
from database.session import async_session

logger = structlog.get_logger()

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error("unhandled_exception", error=str(e), trace=error_trace)
            
            user_id = None
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
                
            async with async_session() as session:
                audit = AuditLog(
                    event_code="CRITICAL",
                    actor_id=user_id,
                    level="CRITICAL",
                    detail={"error": str(e), "trace": error_trace}
                )
                session.add(audit)
                await session.commit()
                
            bot = data["bot"]
            await bot.send_message(
                settings.bot.owner_id,
                f"🚨 **CRITICAL ERROR**\n\nUser: {user_id}\nError: {str(e)}\n\nCheck logs for full traceback."
            )
            
            return
