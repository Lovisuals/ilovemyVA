"migrations/versions/0001_initial.py"

"""initial

Revision ID: 0001
Revises:
Create Date: 2024-04-23 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('bot_users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=True),
        sa.Column('full_name', sa.String(length=256), nullable=False),
        sa.Column('role', sa.Enum('SUPERADMIN', 'ADMIN', 'USER', 'PENDING', name='userrole'), nullable=False),
        sa.Column('verification_code', sa.String(length=16), nullable=True),
        sa.Column('code_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('code_used', sa.Boolean(), nullable=False),
        sa.Column('promoted_by', sa.BigInteger(), nullable=True),
        sa.Column('invited_by', sa.BigInteger(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['invited_by'], ['bot_users.id'], ),
        sa.ForeignKeyConstraint(['promoted_by'], ['bot_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('content_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('bucket', sa.Enum('DRAFTS', 'SCHEDULED', 'PUBLISHED', 'ARCHIVE', name='contentbucket'), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('parse_mode', sa.Enum('HTML', 'MARKDOWN_V2', name='parsemode'), nullable=False),
        sa.Column('file_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('media_group_id', sa.String(length=64), nullable=True),
        sa.Column('has_poll', sa.Boolean(), nullable=False),
        sa.Column('poll_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recurrence', sa.String(length=20), nullable=True),
        sa.Column('tz_name', sa.String(length=64), nullable=False),
        sa.Column('scheduler_job_id', sa.String(length=128), nullable=True),
        sa.Column('tone_score', sa.Float(), nullable=True),
        sa.Column('tone_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('disclaimer_appended', sa.Boolean(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_items_bucket'), 'content_items', ['bucket'], unique=False)
    op.create_index(op.f('ix_content_items_content_hash'), 'content_items', ['content_hash'], unique=False)
    op.create_index(op.f('ix_content_items_created_at'), 'content_items', ['created_at'], unique=False)
    op.create_index(op.f('ix_content_items_scheduled_at'), 'content_items', ['scheduled_at'], unique=False)

    op.create_table('broadcast_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('content_id', sa.UUID(), nullable=False),
        sa.Column('target_chat_id', sa.BigInteger(), nullable=False),
        sa.Column('target_name', sa.String(length=128), nullable=True),
        sa.Column('message_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'SKIPPED_DEDUP', name='broadcaststatus'), nullable=False),
        sa.Column('error_detail', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_broadcast_logs_content_id'), 'broadcast_logs', ['content_id'], unique=False)

    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('event_code', sa.String(length=64), nullable=False),
        sa.Column('actor_id', sa.BigInteger(), nullable=True),
        sa.Column('target_id', sa.String(length=128), nullable=True),
        sa.Column('detail', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('level', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_event_code'), 'audit_logs', ['event_code'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)

    op.create_table('storage_records',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('file_id', sa.String(length=256), nullable=False),
        sa.Column('file_unique_id', sa.String(length=128), nullable=False),
        sa.Column('file_type', sa.Enum('PHOTO', 'VIDEO', 'DOCUMENT', 'AUDIO', 'VOICE', 'ANIMATION', name='filetype'), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('storage_message_id', sa.BigInteger(), nullable=False),
        sa.Column('storage_channel_id', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_by', sa.BigInteger(), nullable=False),
        sa.Column('content_item_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_unique_id')
    )

    op.create_table('rate_limit_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('moderation_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('content_id', sa.UUID(), nullable=False),
        sa.Column('moderator_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('moderation_events')
    op.drop_table('rate_limit_events')
    op.drop_table('storage_records')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_code'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_broadcast_logs_content_id'), table_name='broadcast_logs')
    op.drop_table('broadcast_logs')
    op.drop_index(op.f('ix_content_items_scheduled_at'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_created_at'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_content_hash'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_bucket'), table_name='content_items')
    op.drop_table('content_items')
    op.drop_table('bot_users')

    sa.Enum(name='userrole').drop(op.get_bind())
    sa.Enum(name='contentbucket').drop(op.get_bind())
    sa.Enum(name='parsemode').drop(op.get_bind())
    sa.Enum(name='broadcaststatus').drop(op.get_bind())
    sa.Enum(name='filetype').drop(op.get_bind())
