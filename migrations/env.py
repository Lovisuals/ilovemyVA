import os
import sys
from logging.config import fileConfig
import sqlalchemy as sa
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv()
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from database.base import Base
import bot.models

target_metadata = Base.metadata

def get_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    # Normalise all known prefixes to plain psycopg2 (sync) format
    for asyncpg_prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if url.startswith(asyncpg_prefix):
            url = "postgresql://" + url[len(asyncpg_prefix):]
            break
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    sep = "&" if "?" in url else "?"
    url += f"{sep}connect_timeout=10"
    return url

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        connection.execute(sa.text("SET lock_timeout = '30s'"))
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
