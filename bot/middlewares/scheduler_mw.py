"""
Scheduler Injection Middleware
===============================

Injects the shared ``AsyncScheduler`` instance from ``dp["scheduler"]`` into
the handler data dict so that any router handler can receive it as:

    async def my_handler(..., scheduler: AsyncScheduler):

This is necessary because aiogram does NOT automatically propagate
``dp["key"]`` values into handler dependencies — they must be explicitly
injected by a middleware.

Without this middleware, every handler that needs the scheduler will receive
``None`` and fail silently (as was the case for ``target_confirm`` in
``scheduling.py``).
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

logger = logging.getLogger(__name__)


class SchedulerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        dispatcher = data.get("dispatcher")
        if dispatcher is not None:
            scheduler = dispatcher.get("scheduler")
            if scheduler is not None:
                data["scheduler"] = scheduler
            else:
                # Log only once at debug level to avoid log spam
                logger.debug(
                    "SCHEDULER_MW: scheduler not yet available in dp "
                    "(startup still in progress or scheduler failed to initialise)"
                )
        return await handler(event, data)
