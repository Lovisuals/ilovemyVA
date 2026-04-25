import os
import sys
from logging.config import fileConfig
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
    for asyncpg_prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if url.startswith(asyncpg_prefix):
            url = "postgresql://" + url[len(asyncpg_prefix):]
            break
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url += f"{sep}sslmode=prefer"
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
    db_url = get_url()
    configuration["sqlalchemy.url"] = db_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"options": "-c lock_timeout=30000"},
    )

    masked_url = db_url.split("@")[-1] if "@" in db_url else "..."
    print(f"DEBUG: Connecting to {masked_url}...")
    
    try:
        with connectable.connect() as connection:
            print("DEBUG: Connection established. Configuring context...")
            context.configure(
                connection=connection, 
                target_metadata=target_metadata,
                compare_type=True
            )
            
            print("DEBUG: Beginning transaction...")
            with context.begin_transaction():
                print("DEBUG: Running migrations...")
                context.run_migrations()
                print("DEBUG: Migrations complete.")
    except Exception as e:
        print(f"ERROR: Migration connection/run failed: {e}")
        raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
