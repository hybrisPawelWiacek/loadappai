"""Update toll rates to new format.

Revision ID: 002_update_toll_rates
Revises: 004
Create Date: 2024-12-22 21:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import json


# revision identifiers, used by Alembic.
revision = '002_update_toll_rates'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Get all cost settings records
    connection = op.get_bind()
    result = connection.execute(text("SELECT id, toll_rates FROM cost_settings"))
    rows = result.fetchall()

    # Update each record
    for row in rows:
        id, toll_rates = row
        if toll_rates:
            # Parse JSON if it's a string
            if isinstance(toll_rates, str):
                toll_rates = json.loads(toll_rates)

            # Convert each toll rate to the new format
            new_toll_rates = {}
            for country, rate in toll_rates.items():
                if isinstance(rate, (float, int)):
                    new_toll_rates[country] = {
                        "highway": float(rate),
                        "national": float(rate) * 0.7
                    }
                else:
                    # Already in new format
                    new_toll_rates[country] = rate

            # Update the record
            connection.execute(
                text("UPDATE cost_settings SET toll_rates = :toll_rates WHERE id = :id"),
                {"toll_rates": json.dumps(new_toll_rates), "id": id}
            )


def downgrade():
    # Convert back to old format if needed
    connection = op.get_bind()
    result = connection.execute(text("SELECT id, toll_rates FROM cost_settings"))
    rows = result.fetchall()

    for row in rows:
        id, toll_rates = row
        if toll_rates:
            # Parse JSON if it's a string
            if isinstance(toll_rates, str):
                toll_rates = json.loads(toll_rates)

            # Convert back to old format using highway rates
            old_toll_rates = {
                country: rates["highway"] if isinstance(rates, dict) else rates
                for country, rates in toll_rates.items()
            }

            # Update the record
            connection.execute(
                text("UPDATE cost_settings SET toll_rates = :toll_rates WHERE id = :id"),
                {"toll_rates": json.dumps(old_toll_rates), "id": id}
            )
