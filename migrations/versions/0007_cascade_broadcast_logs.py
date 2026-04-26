"""cascade broadcast_logs

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-26 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing FK
    op.drop_constraint('broadcast_logs_content_id_fkey', 'broadcast_logs', type_='foreignkey')
    # Re-create with CASCADE
    op.create_foreign_key(
        'broadcast_logs_content_id_fkey',
        'broadcast_logs', 'content_items',
        ['content_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    op.drop_constraint('broadcast_logs_content_id_fkey', 'broadcast_logs', type_='foreignkey')
    op.create_foreign_key(
        'broadcast_logs_content_id_fkey',
        'broadcast_logs', 'content_items',
        ['content_id'], ['id']
    )
