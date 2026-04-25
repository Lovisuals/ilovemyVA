from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from sqlalchemy import create_engine
from bot.config import settings

async def setup_scheduler() -> AsyncScheduler:
    sync_url = settings.database.url
    if sync_url.startswith("postgres://"):
        sync_url = sync_url.replace("postgres://", "postgresql://", 1)
    elif sync_url.startswith("postgresql+asyncpg://"):
        sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    engine = create_engine(sync_url)
    data_store = SQLAlchemyDataStore(engine)
    scheduler = AsyncScheduler(data_store=data_store)
    return scheduler
