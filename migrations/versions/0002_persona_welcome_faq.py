"""persona_welcome_faq

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'bot_personas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=True),
        sa.Column('signature', sa.String(length=256), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bot_personas_is_active', 'bot_personas', ['is_active'])

    op.create_table(
        'welcome_configs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_welcome_configs_chat_id', 'welcome_configs', ['chat_id'])

    op.create_table(
        'faq_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('trigger', sa.String(length=256), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('match_type', sa.String(length=16), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_faq_entries_is_active', 'faq_entries', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_faq_entries_is_active', table_name='faq_entries')
    op.drop_table('faq_entries')
    op.drop_index('ix_welcome_configs_chat_id', table_name='welcome_configs')
    op.drop_table('welcome_configs')
    op.drop_index('ix_bot_personas_is_active', table_name='bot_personas')
    op.drop_table('bot_personas')
