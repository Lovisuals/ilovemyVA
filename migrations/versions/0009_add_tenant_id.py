"""add tenant_id to tenant-scoped tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-09

Adds tenant_id (BIGINT NOT NULL DEFAULT 0) to:
  - content_items
  - broadcast_logs
  - moderation_events
  - storage_records
  - audit_logs

DEFAULT 0 is a sentinel for "legacy / pre-multi-tenant rows".
The application writes the real OWNER_ID on every new row via TenantContext.

Phase 2 migration will backfill DEFAULT 0 rows to the actual owner_id once
TenantRegistry is live.
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

# Tables that need tenant_id + an index
_TABLES = [
    "content_items",
    "broadcast_logs",
    "moderation_events",
    "storage_records",
    "audit_logs",
]


def upgrade() -> None:
    for table in _TABLES:
        # Add column — nullable first so existing rows don't violate NOT NULL
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                sa.BigInteger(),
                nullable=True,
                server_default="0",
            ),
        )
        # Backfill existing rows with sentinel 0
        op.execute(f"UPDATE {table} SET tenant_id = 0 WHERE tenant_id IS NULL")
        # Now make it NOT NULL
        op.alter_column(table, "tenant_id", nullable=False, server_default=None)
        # Composite index: tenant + the most common filter column
        if table == "content_items":
            op.create_index(
                f"ix_{table}_tenant_bucket",
                table,
                ["tenant_id", "bucket"],
            )
            op.create_index(
                f"ix_{table}_tenant_created_at",
                table,
                ["tenant_id", "created_at"],
            )
        else:
            op.create_index(
                f"ix_{table}_tenant_id",
                table,
                ["tenant_id"],
            )


def downgrade() -> None:
    for table in _TABLES:
        if table == "content_items":
            op.drop_index(f"ix_{table}_tenant_created_at", table_name=table)
            op.drop_index(f"ix_{table}_tenant_bucket", table_name=table)
        else:
            op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")
