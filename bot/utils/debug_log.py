"""
DEPRECATED — Compatibility shim.
=================================

All callers should migrate to ``bot.utils.sniffer.sniffer``.

This file is kept only so that any stale import of ``write_debug_log`` does
not crash the process.  It silently redirects into the production sniffer.
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def write_debug_log(
    *, run_id: str, hypothesis_id: str, location: str, message: str, data: dict[str, Any]
) -> None:
    """
    Legacy shim — fires into the sniffer (best-effort, non-blocking).
    """
    try:
        from bot.utils.sniffer import sniffer

        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(sniffer.capture(
                source=f"debug_log_compat:{location}",
                event=hypothesis_id,
                severity="WARNING",
                run_id=run_id,
                message=message,
                **data,
            ))
        else:
            logger.warning(
                "DEPRECATED debug_log (no event loop): %s | %s | %s",
                location, message, data,
            )
    except Exception as e:
        logger.warning("debug_log shim failed: %s", e)
