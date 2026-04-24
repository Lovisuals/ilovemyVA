"""connected_chats_structured_drafts

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-24

"""
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All statements use IF NOT EXISTS so this migration is safe to re-run
    # if a previous attempt partially succeeded before rolling back.
    op.execute("""
        CREATE TABLE IF NOT EXISTS connected_chats (
            chat_id     BIGINT PRIMARY KEY,
            title       VARCHAR(256) NOT NULL,
            username    VARCHAR(128),
            chat_type   VARCHAR(16)  NOT NULL,
            bot_status  VARCHAR(16)  NOT NULL,
            is_broadcast_target BOOLEAN NOT NULL DEFAULT true,
            added_at    TIMESTAMPTZ  NOT NULL,
            last_active_at TIMESTAMPTZ
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_connected_chats_bot_status "
        "ON connected_chats (bot_status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_connected_chats_is_target "
        "ON connected_chats (is_broadcast_target)"
    )
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS subject      VARCHAR(256)")
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS sched_days   VARCHAR(64)")
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS sched_time   VARCHAR(8)")
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS post_type    VARCHAR(12)")
    op.execute("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS target_chat_ids TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE content_items DROP COLUMN IF EXISTS target_chat_ids")
    op.execute("ALTER TABLE content_items DROP COLUMN IF EXISTS post_type")
    op.execute("ALTER TABLE content_items DROP COLUMN IF EXISTS sched_time")
    op.execute("ALTER TABLE content_items DROP COLUMN IF EXISTS sched_days")
    op.execute("ALTER TABLE content_items DROP COLUMN IF EXISTS subject")
    op.execute("DROP INDEX IF EXISTS ix_connected_chats_is_target")
    op.execute("DROP INDEX IF EXISTS ix_connected_chats_bot_status")
    op.execute("DROP TABLE IF EXISTS connected_chats")
