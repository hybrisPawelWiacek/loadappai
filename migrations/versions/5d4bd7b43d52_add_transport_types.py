"""add transport types

Revision ID: 5d4bd7b43d52
Revises: 001
Create Date: 2024-12-22 16:56:00.749761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '5d4bd7b43d52'
down_revision: Union[str, None] = None  # This is our first migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Create an ad-hoc table representation for transport_types
transport_types_table = table('transport_types',
    column('id', sa.String),
    column('name', sa.String),
    column('capacity', sa.Float),
    column('emissions_class', sa.String),
    column('fuel_consumption_empty', sa.Float),
    column('fuel_consumption_loaded', sa.Float),
    column('extra_data', sa.JSON)
)


def upgrade() -> None:
    # Drop existing transport_types table if it exists
    op.execute('DROP TABLE IF EXISTS transport_types')

    # Create transport_types table
    op.create_table(
        'transport_types',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('capacity', sa.Float(), nullable=False),
        sa.Column('emissions_class', sa.String(), nullable=False),
        sa.Column('fuel_consumption_empty', sa.Float(), nullable=False),
        sa.Column('fuel_consumption_loaded', sa.Float(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Insert initial transport types
    op.bulk_insert(transport_types_table,
        [
            {
                'id': 'truck',
                'name': 'Standard Truck',
                'capacity': 24000.0,  # 24 tons
                'emissions_class': 'EURO6',
                'fuel_consumption_empty': 25.0,  # L/100km
                'fuel_consumption_loaded': 32.0,  # L/100km
                'extra_data': {
                    'length_m': 13.6,
                    'width_m': 2.4,
                    'height_m': 2.7,
                    'volume_m3': 86.0
                }
            },
            {
                'id': 'van',
                'name': 'Delivery Van',
                'capacity': 3500.0,  # 3.5 tons
                'emissions_class': 'EURO6',
                'fuel_consumption_empty': 12.0,  # L/100km
                'fuel_consumption_loaded': 15.0,  # L/100km
                'extra_data': {
                    'length_m': 4.5,
                    'width_m': 1.8,
                    'height_m': 2.0,
                    'volume_m3': 14.0
                }
            },
            {
                'id': 'trailer',
                'name': 'Semi-Trailer',
                'capacity': 40000.0,  # 40 tons
                'emissions_class': 'EURO6',
                'fuel_consumption_empty': 28.0,  # L/100km
                'fuel_consumption_loaded': 38.0,  # L/100km
                'extra_data': {
                    'length_m': 16.5,
                    'width_m': 2.55,
                    'height_m': 4.0,
                    'volume_m3': 100.0
                }
            }
        ]
    )

    # For SQLite, we need to recreate the table to add foreign key
    # Create new table
    op.execute('PRAGMA foreign_keys=off')
    
    # Create new routes table with foreign key
    op.execute('''
        CREATE TABLE routes_new (
            id VARCHAR NOT NULL PRIMARY KEY,
            origin JSON NOT NULL,
            destination JSON NOT NULL,
            pickup_time DATETIME NOT NULL,
            delivery_time DATETIME NOT NULL,
            transport_type VARCHAR NOT NULL REFERENCES transport_types(id),
            cargo_id VARCHAR REFERENCES cargoes(id),
            distance_km FLOAT NOT NULL,
            duration_hours FLOAT NOT NULL,
            empty_driving JSON,
            is_feasible BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            route_metadata JSON,
            country_segments JSON,
            cargo_specs JSON,
            vehicle_specs JSON,
            time_windows JSON,
            extra_data JSON
        )
    ''')
    
    # Copy data from old table to new table
    op.execute('''
        INSERT INTO routes_new 
        SELECT * FROM routes
    ''')
    
    # Drop old table
    op.execute('DROP TABLE routes')
    
    # Rename new table to routes
    op.execute('ALTER TABLE routes_new RENAME TO routes')
    
    op.execute('PRAGMA foreign_keys=on')


def downgrade() -> None:
    # Drop foreign key constraint by recreating the table without it
    op.execute('PRAGMA foreign_keys=off')
    
    # Create new routes table without foreign key
    op.execute('''
        CREATE TABLE routes_new (
            id VARCHAR NOT NULL PRIMARY KEY,
            origin JSON NOT NULL,
            destination JSON NOT NULL,
            pickup_time DATETIME NOT NULL,
            delivery_time DATETIME NOT NULL,
            transport_type VARCHAR NOT NULL,
            cargo_id VARCHAR REFERENCES cargoes(id),
            distance_km FLOAT NOT NULL,
            duration_hours FLOAT NOT NULL,
            empty_driving JSON,
            is_feasible BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            route_metadata JSON,
            country_segments JSON,
            cargo_specs JSON,
            vehicle_specs JSON,
            time_windows JSON,
            extra_data JSON
        )
    ''')
    
    # Copy data
    op.execute('''
        INSERT INTO routes_new 
        SELECT * FROM routes
    ''')
    
    # Drop old table
    op.execute('DROP TABLE routes')
    
    # Rename new table
    op.execute('ALTER TABLE routes_new RENAME TO routes')
    
    op.execute('PRAGMA foreign_keys=on')
    
    # Drop transport_types table
    op.drop_table('transport_types')
