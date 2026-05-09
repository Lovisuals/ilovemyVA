import time
from typing import Any, Awaitable, Callable, Dict
import structlog
from aiogram import BaseMiddleware
from aiogram.types import Update
from bot.utils.debug_log import write_debug_log
logger = structlog.get_logger()
class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        start_time = time.time()
        user_id = "unknown"
        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id
        update_type = event.event_type
        write_debug_log(
            run_id="pre-fix",
            hypothesis_id="H2",
            location="bot/middlewares/logging_mw.py:__call__",
            message="Update reached logging middleware",
            data={"user_id": user_id, "update_type": update_type},
        )
        response = await handler(event, data)
        duration = time.time() - start_time
        logger.info(
            "update_processed",
            user_id=user_id,
            update_type=update_type,
            duration_ms=round(duration * 1000, 2)
        )
        write_debug_log(
            run_id="pre-fix",
            hypothesis_id="H2",
            location="bot/middlewares/logging_mw.py:__call__",
            message="Update finished handler chain",
            data={"user_id": user_id, "update_type": update_type, "duration_ms": round(duration * 1000, 2)},
        )
        return response
