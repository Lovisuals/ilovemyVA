"""expand sched_time

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-25 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('content_items', 'sched_time',
               existing_type=sa.String(length=8),
               type_=sa.String(length=128),
               existing_nullable=True)

def downgrade():
    op.alter_column('content_items', 'sched_time',
               existing_type=sa.String(length=128),
               type_=sa.String(length=8),
               existing_nullable=True)
