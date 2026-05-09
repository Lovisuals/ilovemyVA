import uuid
import logging
import traceback
from datetime import datetime, timedelta, timezone
from apscheduler import AsyncScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.content_item import ContentItem, ContentBucket
from bot.utils.sniffer import sniffer
logger = logging.getLogger(__name__)
class SchedulerService:
    @staticmethod
    async def register_job(
        session: AsyncSession,
        scheduler: AsyncScheduler,
        item_id: uuid.UUID,
        times: list[str],
        recurrence: str,
        tz_str: str = "Africa/Lagos",
    ) -> str:
        """
        Register one or more APScheduler schedules for a content item.
        For ``recurrence='daily'`` or ``'weekly'``, a CronTrigger is used so
        APScheduler keeps re-firing the job indefinitely (until explicitly
        cancelled).  For ``recurrence='once'``, a DateTrigger fires exactly once.
        Returns a comma-separated string of schedule IDs stored on the content
        item's ``scheduler_job_id`` column.
        """
        from bot.scheduler.jobs import publish_content_job
        import pytz
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.date import DateTrigger
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        job_ids = []
        for idx, time_str in enumerate(times):
            job_id = f"{item_id}_{idx}"
            job_ids.append(job_id)
            if ":" in time_str:
                h, m = map(int, time_str.split(":"))
            else:
                h, m = int(time_str[:2]), int(time_str[2:])
            if recurrence == "daily":
                trigger = CronTrigger(hour=h, minute=m, timezone=tz_str)
            elif recurrence == "weekly":
                trigger = CronTrigger(day_of_week=now.weekday(), hour=h, minute=m, timezone=tz_str)
            else:
                run_at = tz.localize(datetime(now.year, now.month, now.day, h, m))
                if run_at < now:
                    run_at += timedelta(days=1)
                trigger = DateTrigger(run_time=run_at.astimezone(pytz.UTC))
            # SIDE EFFECT: Registers a background job in APScheduler. Why necessary and unavoidable: This is the core purpose of the service—to ensure content is published at the designated time.
            await scheduler.add_schedule(
                publish_content_job,
                trigger,
                id=job_id,
                args=[str(item_id)],
            )
            logger.info(
                "SCHEDULER_SVC: registered schedule id=%s trigger=%s recurrence=%s",
                job_id, trigger, recurrence,
            )
        combined_job_ids = ",".join(job_ids)
        result = await session.execute(
            select(ContentItem).where(ContentItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.scheduler_job_id = combined_job_ids
            item.sched_time = ",".join(times)
            item.recurrence = recurrence
            if recurrence == "once":
                t0 = times[0]
                if ":" in t0:
                    h, m = map(int, t0.split(":"))
                else:
                    h, m = int(t0[:2]), int(t0[2:])
                run_at = tz.localize(datetime(now.year, now.month, now.day, h, m))
                if run_at < now:
                    run_at += timedelta(days=1)
                item.scheduled_at = run_at.astimezone(pytz.UTC)
            else:
                item.scheduled_at = datetime.now(timezone.utc)
            item.recurrence = recurrence
            item.bucket = ContentBucket.SCHEDULED
            # SIDE EFFECT: Persists schedule state to database. Why necessary and unavoidable: Necessary to maintain state across restarts and keep UI in sync with the background scheduler.
            try:
                await session.commit()
                logger.info(
                    "SCHEDULER_SVC: item %s committed — bucket=SCHEDULED recurrence=%s jobs=%s",
                    item_id, recurrence, combined_job_ids,
                )
            except Exception as commit_err:
                logger.error(
                    "SCHEDULER_SVC: DB commit failed for item %s: %s",
                    item_id, commit_err, exc_info=True,
                )
                await sniffer.capture(
                    source="SchedulerService.register_job",
                    event="db_commit_failed",
                    severity="ERROR",
                    item_id=str(item_id),
                    error=str(commit_err),
                    traceback=traceback.format_exc(),
                )
                await session.rollback()
                raise
        else:
            logger.warning(
                "SCHEDULER_SVC: item %s not found in DB — schedules registered but item not updated",
                item_id,
            )
            await sniffer.capture(
                source="SchedulerService.register_job",
                event="item_not_found_after_schedule",
                severity="WARNING",
                item_id=str(item_id),
            )
        return combined_job_ids
    @staticmethod
    async def cancel_job(scheduler: AsyncScheduler, job_ids: str) -> None:
        """Cancel one or more APScheduler schedules by their comma-separated IDs."""
        if not job_ids:
            return
        for job_id in job_ids.split(","):
            job_id = job_id.strip()
            if not job_id:
                continue
            try:
                await scheduler.remove_schedule(job_id)
                logger.info("SCHEDULER_SVC: cancelled schedule id=%s", job_id)
            except Exception as cancel_err:
                logger.warning(
                    "SCHEDULER_SVC: failed to cancel schedule id=%s: %s",
                    job_id, cancel_err,
                )
                await sniffer.capture(
                    source="SchedulerService.cancel_job",
                    event="cancel_failed",
                    severity="WARNING",
                    job_id=job_id,
                    error=str(cancel_err),
                )
