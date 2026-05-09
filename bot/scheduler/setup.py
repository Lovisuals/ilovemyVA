import logging
from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from sqlalchemy.ext.asyncio import create_async_engine
from bot.config import settings
logger = logging.getLogger(__name__)
async def setup_scheduler() -> AsyncScheduler:
    """
    Create an APScheduler 4.x ``AsyncScheduler`` backed by the same Postgres
    instance the rest of the bot uses.
    IMPORTANT: We use an **async** engine here instead of a synchronous one.
    Using ``create_engine`` (sync) inside an async application will block the
    event loop on every scheduler DB operation, causing silent job-dispatch
    stalls under load.
    """
    async_url = settings.database.dsn
    engine = create_async_engine(async_url)
    data_store = SQLAlchemyDataStore(engine)
    scheduler = AsyncScheduler(data_store=data_store)
    logger.info(
        "SCHEDULER_SETUP: created AsyncScheduler with async data store url=%s",
        async_url[:40] + "...",
    )
    return scheduler
