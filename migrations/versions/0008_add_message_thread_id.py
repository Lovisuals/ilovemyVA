"""add message_thread_id to connected_chats

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-26 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('connected_chats', sa.Column('message_thread_id', sa.BigInteger(), nullable=True))

def downgrade():
    op.drop_column('connected_chats', 'message_thread_id')
