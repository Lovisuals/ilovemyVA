import asyncio
import logging
import traceback
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Update
from bot.config import settings
from bot.models.audit_log import AuditLog
from database.session import async_session
from bot.utils.sniffer import sniffer
logger = logging.getLogger(__name__)
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
            logger.error("Unhandled exception: %s\n%s", e, error_trace)
            asyncio.ensure_future(sniffer.capture(
                source="ErrorHandlerMiddleware",
                event="unhandled_exception",
                severity="CRITICAL",
                error=str(e),
                traceback=error_trace,
            ))
            user_id = None
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id
            try:
                async with async_session() as session:
                    audit = AuditLog(
                        event_code="CRITICAL",
                        actor_id=user_id,
                        level="CRITICAL",
                        detail={"error": str(e), "trace": error_trace},
                    )
                    session.add(audit)
                    await session.commit()
            except Exception as audit_err:
                logger.warning("Failed to write audit log: %s", audit_err)
            try:
                bot = data.get("bot")
                if bot:
                    await bot.send_message(
                        settings.bot.owner_id,
                        f"CRITICAL ERROR\n\nUser: {user_id}\nError: {str(e)[:500]}\n\nCheck logs for full traceback.",
                        parse_mode=None
                    )
            except Exception as notify_err:
                logger.warning("Failed to notify owner: %s", notify_err)
            return
