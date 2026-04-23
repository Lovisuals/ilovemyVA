"database/session.py"

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings

engine_kwargs = {
    "echo": settings.database.echo,
}

if not settings.database.dsn.startswith("sqlite"):
    engine_kwargs["pool_size"] = settings.database.pool_size
    engine_kwargs["pool_timeout"] = settings.database.pool_timeout

engine = create_async_engine(
    settings.database.dsn,
    **engine_kwargs,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
