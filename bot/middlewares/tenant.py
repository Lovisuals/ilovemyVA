"""
bot/middlewares/tenant.py — TenantMiddleware

Injects a TenantContext into data["tenant"] for every update.

In Phase 1 (single-tenant):
  - Reads OWNER_ID + env vars, returns one fixed TenantContext per instance.
  - Zero behaviour change for existing handlers that don't declare `tenant`.

In Phase 2+ (multi-tenant control plane):
  - Replace _resolve_tenant() to look up TenantRegistry by bot_user.id or
    the Railway instance's OWNER_ID, returning per-subscriber config from DB.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

from bot.config import settings
from bot.tenant import TenantContext

logger = logging.getLogger(__name__)

# Module-level singleton for single-tenant deployments.
# In multi-tenant mode, resolve per-request from TenantRegistry.
_SINGLETON: TenantContext | None = None


def _get_singleton() -> TenantContext:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = TenantContext.from_env(owner_id=settings.bot.owner_id)
        logger.info(
            "TENANT: singleton context built tenant_id=%s domain=%s tz=%s",
            _SINGLETON.tenant_id,
            _SINGLETON.service_domain,
            _SINGLETON.tz_default,
        )
    return _SINGLETON


class TenantMiddleware(BaseMiddleware):
    """
    Injects data["tenant"] = TenantContext into every update.

    Handlers opt-in by declaring `tenant: TenantContext` in their signature.
    Handlers that don't declare it are unaffected (aiogram ignores extra data keys).
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        ctx = _get_singleton()
        data["tenant"] = ctx
        logger.debug(
            "TENANT: injected tenant_id=%s for event_type=%s",
            ctx.tenant_id,
            event.event_type,
        )
        return await handler(event, data)
