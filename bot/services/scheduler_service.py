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
        run_at: datetime,
        recurrence: str,
    ) -> str:
        from bot.scheduler.jobs import publish_content_job

        job_id = str(item_id)
        await scheduler.add_schedule(
            publish_content_job,
            DateTrigger(run_time=run_at),
            id=job_id,
            args=[str(item_id)],
        )

        result = await session.execute(
            select(ContentItem).where(ContentItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.scheduler_job_id = job_id
            item.scheduled_at = run_at
            item.recurrence = recurrence
            item.bucket = ContentBucket.SCHEDULED
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return job_id

    @staticmethod
    async def cancel_job(scheduler: AsyncScheduler, job_id: str) -> None:
        try:
            await scheduler.remove_schedule(job_id)
        except Exception:
            pass
