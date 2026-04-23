"database/session.py"

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings

engine = create_async_engine(
    settings.database.dsn,
    echo=settings.database.echo,
    pool_size=settings.database.pool_size,
    pool_timeout=settings.database.pool_timeout,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
