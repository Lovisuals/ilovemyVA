import uuid
from datetime import datetime
from apscheduler._schedulers.async_ import AsyncScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.content_item import ContentItem, ContentBucket


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
            
            h, m = map(int, time_str.split(":"))
            
            if recurrence == "daily":
                trigger = CronTrigger(hour=h, minute=m, timezone=tz_str)
            elif recurrence == "weekly":
                trigger = CronTrigger(day_of_week=now.weekday(), hour=h, minute=m, timezone=tz_str)
            else: # once
                run_at = tz.localize(datetime(now.year, now.month, now.day, h, m))
                if run_at < now:
                    run_at += timedelta(days=1)
                trigger = DateTrigger(run_time=run_at.astimezone(pytz.UTC))

            await scheduler.add_schedule(
                publish_content_job,
                trigger,
                id=job_id,
                args=[str(item_id)],
            )

        combined_job_ids = ",".join(job_ids)

        result = await session.execute(
            select(ContentItem).where(ContentItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.scheduler_job_id = combined_job_ids
            # Keep scheduled_at for UI purposes, using the first time
            if recurrence == "once":
                h, m = map(int, times[0].split(":"))
                run_at = tz.localize(datetime(now.year, now.month, now.day, h, m))
                if run_at < now:
                    run_at += timedelta(days=1)
                item.scheduled_at = run_at.astimezone(pytz.UTC)
            else:
                item.scheduled_at = datetime.now(timezone.utc)
                
            item.recurrence = recurrence
            item.bucket = ContentBucket.SCHEDULED
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return combined_job_ids

    @staticmethod
    async def cancel_job(scheduler: AsyncScheduler, job_ids: str) -> None:
        if not job_ids:
            return
        for job_id in job_ids.split(","):
            try:
                await scheduler.remove_schedule(job_id)
            except Exception:
                pass
