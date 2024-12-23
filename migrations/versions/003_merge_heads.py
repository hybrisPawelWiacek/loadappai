"""merge heads

Revision ID: 003_merge_heads
Revises: 5d4bd7b43d52, 002_update_toll_rates
Create Date: 2024-12-22 21:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_merge_heads'
down_revision = ('5d4bd7b43d52', '002_update_toll_rates')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
