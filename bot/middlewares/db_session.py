from typing import Any, Awaitable, Callable, Dict
import logging
from aiogram import BaseMiddleware
from aiogram.types import Update
from database.session import async_session
logger = logging.getLogger(__name__)
class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            logger.info("DBSESSION: opening session for event_type=%s", event.event_type)
            async with async_session() as session:
                data["session"] = session
                logger.info("DBSESSION: session injected for event_type=%s", event.event_type)
                return await handler(event, data)
        except Exception as e:
            logger.error("DBSESSION: Middleware failed before handler completion: %s", e, exc_info=True)
            raise
