"""group_settings_moderation

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id      BIGINT PRIMARY KEY,
            mod_enabled  BOOLEAN NOT NULL DEFAULT false,
            link_filter  BOOLEAN NOT NULL DEFAULT false,
            warn_limit   INTEGER NOT NULL DEFAULT 3,
            keyword_list TEXT,
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_warnings (
            chat_id        BIGINT NOT NULL,
            user_id        BIGINT NOT NULL,
            warn_count     INTEGER NOT NULL DEFAULT 0,
            last_reason    VARCHAR(256),
            last_warned_at TIMESTAMPTZ,
            PRIMARY KEY (chat_id, user_id)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_warnings_chat "
        "ON user_warnings (chat_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_warnings_chat")
    op.execute("DROP TABLE IF EXISTS user_warnings")
    op.execute("DROP TABLE IF EXISTS group_settings")