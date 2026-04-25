"""expand scheduler_job_id and sched_time again

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-25 23:24:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('content_items', 'scheduler_job_id',
               existing_type=sa.String(length=128),
               type_=sa.String(length=1024),
               existing_nullable=True)
    op.alter_column('content_items', 'sched_time',
               existing_type=sa.String(length=128),
               type_=sa.String(length=512),
               existing_nullable=True)

def downgrade():
    op.alter_column('content_items', 'scheduler_job_id',
               existing_type=sa.String(length=1024),
               type_=sa.String(length=128),
               existing_nullable=True)
    op.alter_column('content_items', 'sched_time',
               existing_type=sa.String(length=512),
               type_=sa.String(length=128),
               existing_nullable=True)
