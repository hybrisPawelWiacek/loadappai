"""Initial schema

Revision ID: 001
Create Date: 2024-12-22 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision: str = '001'  # This is the current revision
down_revision: Union[str, None] = None  # This is an initial migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tables
    op.create_table(
        'routes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('origin', sa.JSON(), nullable=False),
        sa.Column('destination', sa.JSON(), nullable=False),
        sa.Column('pickup_time', sa.DateTime(), nullable=False),
        sa.Column('delivery_time', sa.DateTime(), nullable=False),
        sa.Column('transport_type', sa.String(), nullable=False),
        sa.Column('cargo_id', sa.String(), nullable=True),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=False),
        sa.Column('empty_driving', sa.JSON(), nullable=True),
        sa.Column('is_feasible', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('route_metadata', sa.JSON(), nullable=True),
        sa.Column('country_segments', sa.JSON(), nullable=True),
        sa.Column('cargo_specs', sa.JSON(), nullable=True),
        sa.Column('vehicle_specs', sa.JSON(), nullable=True),
        sa.Column('time_windows', sa.JSON(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'cost_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('calculation_date', sa.DateTime(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('calculation_method', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('is_final', sa.Boolean(), nullable=False),
        sa.Column('cost_components', sa.JSON(), nullable=False),
        sa.Column('settings_snapshot', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'offers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('cost_id', sa.String(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('margin', sa.Float(), nullable=False),
        sa.Column('final_price', sa.Float(), nullable=False),
        sa.Column('fun_fact', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('modified_by', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
        sa.ForeignKeyConstraint(['cost_id'], ['cost_history.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'offer_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('offer_id', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('margin', sa.Float(), nullable=False),
        sa.Column('final_price', sa.Float(), nullable=False),
        sa.Column('fun_fact', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('changed_by', sa.String(), nullable=True),
        sa.Column('change_reason', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('offer_history')
    op.drop_table('offers')
    op.drop_table('cost_history')
    op.drop_table('routes')
