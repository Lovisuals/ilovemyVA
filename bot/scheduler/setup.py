"bot/scheduler/setup.py"

from apscheduler.schedulers.async_ import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from bot.config import settings

async def setup_scheduler() -> AsyncScheduler:
    # Transform async DSN to sync for APScheduler SQLAlchemy store
    sync_url = settings.database.url
    if sync_url.startswith("postgres://"):
        sync_url = sync_url.replace("postgres://", "postgresql://", 1)

    data_store = SQLAlchemyDataStore(url=sync_url)
    scheduler = AsyncScheduler(data_store)
    return scheduler
