"bot/scheduler/setup.py"

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from bot.config import settings

def setup_scheduler() -> AsyncIOScheduler:
    # Transform async DSN to sync for APScheduler SQLAlchemy store
    sync_url = settings.database.url
    if sync_url.startswith("postgres://"):
        sync_url = sync_url.replace("postgres://", "postgresql://", 1)
        
    jobstores = {
        'default': SQLAlchemyJobStore(url=sync_url)
    }
    
    scheduler = AsyncIOScheduler(jobstores=jobstores)
    return scheduler
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
