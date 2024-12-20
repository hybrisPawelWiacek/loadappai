"""Initial migration

Revision ID: 3f230faf5d1c
Revises: 
Create Date: 2024-12-17 15:45:05.587334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f230faf5d1c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cargoes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('special_requirements', sa.JSON(), nullable=True),
    sa.Column('hazmat', sa.Boolean(), nullable=False),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cost_settings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('fuel_price_per_liter', sa.Float(), nullable=False),
    sa.Column('driver_daily_salary', sa.Float(), nullable=False),
    sa.Column('toll_rates', sa.JSON(), nullable=False),
    sa.Column('overheads', sa.JSON(), nullable=False),
    sa.Column('cargo_factors', sa.JSON(), nullable=False),
    sa.Column('last_modified', sa.DateTime(), nullable=False),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transport_types',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('capacity', sa.Float(), nullable=False),
    sa.Column('emissions_class', sa.String(), nullable=False),
    sa.Column('fuel_consumption_empty', sa.Float(), nullable=False),
    sa.Column('fuel_consumption_loaded', sa.Float(), nullable=False),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('routes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('origin', sa.JSON(), nullable=False),
    sa.Column('destination', sa.JSON(), nullable=False),
    sa.Column('pickup_time', sa.DateTime(), nullable=False),
    sa.Column('delivery_time', sa.DateTime(), nullable=False),
    sa.Column('transport_type', sa.String(), nullable=False),
    sa.Column('cargo_id', sa.String(), nullable=True),
    sa.Column('distance_km', sa.Float(), nullable=False),
    sa.Column('duration_hours', sa.Float(), nullable=False),
    sa.Column('empty_driving', sa.JSON(), nullable=False),
    sa.Column('is_feasible', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['cargo_id'], ['cargoes.id'], ),
    sa.ForeignKeyConstraint(['transport_type'], ['transport_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('offers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('route_id', sa.String(), nullable=False),
    sa.Column('total_cost', sa.Float(), nullable=False),
    sa.Column('margin', sa.Float(), nullable=False),
    sa.Column('final_price', sa.Float(), nullable=False),
    sa.Column('fun_fact', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('offers')
    op.drop_table('routes')
    op.drop_table('transport_types')
    op.drop_table('cost_settings')
    op.drop_table('cargoes')
    # ### end Alembic commands ###
