import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional

from aiogram import Bot
from sqlalchemy import select
from database.session import async_session
from bot.config import settings
from bot.models.broadcast_log import BroadcastLog, BroadcastStatus
from bot.models.content_item import ContentBucket, ContentItem
from bot.utils.sniffer import sniffer

logger = logging.getLogger(__name__)

async def publish_content_job(item_id: str, _bot: Optional[Bot] = None) -> None:
    """
    Scheduled job that publishes a ContentItem to its target chats.

    Recurrence logic:
      - recurrence == 'once'  → mark bucket=PUBLISHED after sending (item is done).
      - recurrence in ('daily', 'weekly') → keep bucket=SCHEDULED so the item
        remains visible in the schedule view and can be fired again by APScheduler.

    The `_bot` parameter allows the main bot instance to be injected (avoids
    creating a new HTTP session on every cron tick). Falls back to a transient
    Bot if not supplied.
    """
    # ── Bot session management ──────────────────────────────────────────────
    _owns_bot = _bot is None
    bot: Bot = _bot or Bot(token=settings.bot.token)

    try:
        async with async_session() as session:
            # ── Fetch content item ──────────────────────────────────────────
            result = await session.execute(
                select(ContentItem).where(ContentItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                logger.warning(
                    "SCHED_JOB [%s]: item not found in DB — schedule may be orphaned",
                    item_id,
                )
                await sniffer.capture(
                    source="publish_content_job",
                    event="item_not_found",
                    item_id=item_id,
                )
                return

            recurrence = (item.recurrence or "once").lower()
            logger.info(
                "SCHED_JOB [%s]: firing — recurrence=%s bucket=%s",
                item_id, recurrence, item.bucket,
            )

            # ── Resolve target chats ────────────────────────────────────────
            target_ids: list[int] = []
            if item.target_chat_ids:
                try:
                    target_ids = json.loads(item.target_chat_ids)
                except Exception as parse_err:
                    logger.warning(
                        "SCHED_JOB [%s]: target_chat_ids parse error: %s",
                        item_id, parse_err,
                    )
                    await sniffer.capture(
                        source="publish_content_job",
                        event="target_chat_ids_parse_error",
                        item_id=item_id,
                        error=str(parse_err),
                    )
            if not target_ids:
                target_ids = [settings.bot.main_channel_id]
                logger.warning(
                    "SCHED_JOB [%s]: no target_chat_ids set — falling back to main_channel_id=%s",
                    item_id, settings.bot.main_channel_id,
                )

            # ── Build message text ─────────────────────────────────────────
            sep = "─" * 28
            header = f"{item.subject}\n{sep}\n" if item.subject else ""
            text = header + (item.text or "")

            try:
                from bot.services.persona_service import PersonaService
                async with async_session() as psession:
                    persona = await PersonaService.get_active(psession)
                    text = PersonaService.apply_to_text(text, persona)
            except Exception as exc:
                logger.warning("SCHED_JOB [%s]: persona fetch failed (non-fatal): %s", item_id, exc)

            # ── Send to each target ────────────────────────────────────────
            from bot.models.connected_chat import ConnectedChat

            sent = 0
            failed = 0
            for chat_id in target_ids:
                chat_info = await session.get(ConnectedChat, chat_id)
                thread_id = chat_info.message_thread_id if chat_info else None

                log = BroadcastLog(
                    content_id=item.id,
                    target_chat_id=chat_id,
                    status=BroadcastStatus.PENDING,
                )
                session.add(log)
                try:
                    msg = await bot.send_message(
                        chat_id,
                        text,
                        message_thread_id=thread_id,
                    )
                    log.status = BroadcastStatus.SENT
                    log.message_id = msg.message_id
                    log.sent_at = datetime.now(timezone.utc)
                    sent += 1
                except Exception as exc:
                    log.status = BroadcastStatus.FAILED
                    log.error_detail = str(exc)[:400]
                    failed += 1
                    logger.warning(
                        "SCHED_JOB [%s]: send failed → chat_id=%s thread=%s error=%s",
                        item_id, chat_id, thread_id, exc,
                    )
                    await sniffer.capture(
                        source="publish_content_job",
                        event="send_failed",
                        item_id=item_id,
                        chat_id=chat_id,
                        thread_id=thread_id,
                        error=str(exc),
                        error_type=type(exc).__name__,
                    )

            # ── Update item state ──────────────────────────────────────────
            # CRITICAL FIX: only retire to PUBLISHED for one-shot posts.
            # Recurring (daily/weekly) posts MUST stay in SCHEDULED so APScheduler
            # keeps firing them and the schedule dashboard shows them correctly.
            now_utc = datetime.now(timezone.utc)
            if recurrence == "once":
                item.bucket = ContentBucket.PUBLISHED
                item.published_at = now_utc
                logger.info(
                    "SCHED_JOB [%s]: one-shot post — marked PUBLISHED", item_id
                )
            else:
                # Keep bucket=SCHEDULED; just stamp last-sent metadata.
                item.published_at = now_utc  # tracks most-recent send
                logger.info(
                    "SCHED_JOB [%s]: recurring post (%s) — keeping bucket=SCHEDULED",
                    item_id, recurrence,
                )

            try:
                await session.commit()
            except Exception as commit_err:
                logger.error(
                    "SCHED_JOB [%s]: DB commit failed after send: %s",
                    item_id, commit_err, exc_info=True,
                )
                await sniffer.capture(
                    source="publish_content_job",
                    event="db_commit_failed",
                    item_id=item_id,
                    error=str(commit_err),
                    traceback=traceback.format_exc(),
                )
                await session.rollback()
                raise

            logger.info(
                "SCHED_JOB [%s]: complete — sent=%d failed=%d/%d recurrence=%s",
                item_id, sent, failed, len(target_ids), recurrence,
            )

    except Exception as outer_err:
        logger.error(
            "SCHED_JOB [%s]: unhandled exception in job: %s",
            item_id, outer_err, exc_info=True,
        )
        await sniffer.capture(
            source="publish_content_job",
            event="unhandled_exception",
            item_id=item_id,
            error=str(outer_err),
            traceback=traceback.format_exc(),
        )
        raise  # re-raise so APScheduler records this run as failed

    finally:
        # Only close the Bot session if we created it ourselves
        if _owns_bot:
            await bot.session.close()
