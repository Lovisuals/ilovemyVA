"""
In-Process Sniffer — Production Silent-Failure Detector
========================================================

Captures structured telemetry from every subsystem (scheduler, DB, middleware)
and persists it to:
  1. Python logger (stderr → Railway log drain) — always available
  2. Database `audit_log` table — queryable from admin panel
  3. Telegram owner notification — for CRITICAL-severity events only

Usage:
    from bot.utils.sniffer import sniffer

    await sniffer.capture(
        source="publish_content_job",
        event="send_failed",
        severity="WARNING",      # DEBUG | INFO | WARNING | ERROR | CRITICAL
        item_id="abc-123",
        chat_id=-100123456,
        error="Chat not found",
    )

Design goals:
  - NEVER raise — all internal errors are swallowed and logged to stderr
  - NEVER block the caller — fire-and-forget for DB/Telegram writes
  - Minimal overhead — skip DB writes for DEBUG/INFO severity
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("sniffer")


class Sniffer:
    """Singleton silent-failure detector for production deployments."""

    _bot = None       # Set once during startup (optional)
    _owner_id = None  # Set once during startup (optional)

    def configure(self, *, bot=None, owner_id: Optional[int] = None) -> None:
        """
        Wire up optional Telegram notification.  Safe to call multiple times.
        """
        if bot is not None:
            self._bot = bot
        if owner_id is not None:
            self._owner_id = owner_id

    async def capture(
        self,
        *,
        source: str,
        event: str,
        severity: str = "WARNING",
        **context: Any,
    ) -> None:
        """
        Record a structured telemetry event.

        Parameters
        ----------
        source : str
            Module / function that produced the event (e.g. "publish_content_job").
        event : str
            Short event name (e.g. "send_failed", "db_commit_failed").
        severity : str
            One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        **context
            Arbitrary key-value pairs merged into the payload.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "ts": now.isoformat(),
            "source": source,
            "event": event,
            "severity": severity,
            **{k: _safe_serialize(v) for k, v in context.items()},
        }

        # ── 1. Always log to stderr (Railway picks this up) ─────────────
        log_line = (
            f"SNIFFER [{severity}] {source}::{event} | "
            + " ".join(f"{k}={v}" for k, v in context.items() if k not in ("traceback",))
        )
        _log_at_level(severity, log_line)

        # ── 2. Persist to audit_log table (WARNING+ only) ──────────────
        if severity in ("WARNING", "ERROR", "CRITICAL"):
            asyncio.ensure_future(self._write_to_db(payload))

        # ── 3. Notify owner via Telegram (CRITICAL only) ───────────────
        if severity == "CRITICAL" and self._bot and self._owner_id:
            asyncio.ensure_future(self._notify_owner(payload))

    # ── internal helpers ───────────────────────────────────────────────

    async def _write_to_db(self, payload: dict) -> None:
        """Best-effort write to audit_log. Never raises."""
        try:
            from database.session import async_session
            from bot.models.audit_log import AuditLog

            async with async_session() as session:
                entry = AuditLog(
                    event_code=f"SNIFFER:{payload['event']}",
                    actor_id=None,
                    level=payload["severity"],
                    detail=payload,
                )
                session.add(entry)
                await session.commit()
        except Exception as db_err:
            logger.warning(
                "SNIFFER: failed to persist event to DB: %s (event=%s)",
                db_err, payload.get("event"),
            )

    async def _notify_owner(self, payload: dict) -> None:
        """Best-effort Telegram alert. Never raises."""
        try:
            msg = (
                f"🔴 **SNIFFER CRITICAL**\n"
                f"Source: `{payload['source']}`\n"
                f"Event: `{payload['event']}`\n"
                f"Time: {payload['ts']}\n"
            )
            error = payload.get("error")
            if error:
                msg += f"Error: `{str(error)[:300]}`\n"
            await self._bot.send_message(self._owner_id, msg)
        except Exception as tg_err:
            logger.warning("SNIFFER: failed to notify owner via Telegram: %s", tg_err)


def _safe_serialize(value: Any) -> Any:
    """Convert a value to something JSON-safe for DB storage."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def _log_at_level(severity: str, message: str) -> None:
    """Route to the correct log level."""
    level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(severity.upper(), logging.WARNING)
    logger.log(level, message)


# ── Module-level singleton ──────────────────────────────────────────────
sniffer = Sniffer()
