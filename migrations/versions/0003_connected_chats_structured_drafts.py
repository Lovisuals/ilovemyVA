"""connected_chats_structured_drafts

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'connected_chats',
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('username', sa.String(length=128), nullable=True),
        sa.Column('chat_type', sa.String(length=16), nullable=False),
        sa.Column('bot_status', sa.String(length=16), nullable=False),
        sa.Column('is_broadcast_target', sa.Boolean(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('chat_id'),
    )
    op.create_index('ix_connected_chats_bot_status', 'connected_chats', ['bot_status'])
    op.create_index('ix_connected_chats_is_target', 'connected_chats', ['is_broadcast_target'])

    op.add_column('content_items', sa.Column('subject', sa.String(length=256), nullable=True))
    op.add_column('content_items', sa.Column('sched_days', sa.String(length=64), nullable=True))
    op.add_column('content_items', sa.Column('sched_time', sa.String(length=8), nullable=True))
    op.add_column('content_items', sa.Column('post_type', sa.String(length=12), nullable=True))
    op.add_column('content_items', sa.Column('target_chat_ids', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('content_items', 'target_chat_ids')
    op.drop_column('content_items', 'post_type')
    op.drop_column('content_items', 'sched_time')
    op.drop_column('content_items', 'sched_days')
    op.drop_column('content_items', 'subject')

    op.drop_index('ix_connected_chats_is_target', table_name='connected_chats')
    op.drop_index('ix_connected_chats_bot_status', table_name='connected_chats')
    op.drop_table('connected_chats')
