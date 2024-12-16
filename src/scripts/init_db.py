"""Database initialization script."""
import logging
from datetime import datetime, timedelta

from src.infrastructure.config import settings
from src.infrastructure.database import init_db
from src.infrastructure.models import Cargo, CostSettings, TransportType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_data() -> None:
    """Create initial data for the application."""
    from src.infrastructure.database import get_db

    with get_db() as db:
        # Create transport types
        transport_types = [
            TransportType(
                id="flatbed_truck",
                name="Flatbed Truck",
                capacity=24000.0,  # 24 tonnes
                emissions_class="EURO6",
                fuel_consumption_empty=25.0,  # L/100km
                fuel_consumption_loaded=32.0,  # L/100km
            ),
            TransportType(
                id="refrigerated_truck",
                name="Refrigerated Truck",
                capacity=22000.0,  # 22 tonnes
                emissions_class="EURO6",
                fuel_consumption_empty=27.0,  # L/100km
                fuel_consumption_loaded=35.0,  # L/100km
            ),
        ]
        db.add_all(transport_types)

        # Create sample cargoes
        cargoes = [
            Cargo(
                id="cargo_001",
                weight=15000.0,  # 15 tonnes
                value=50000.0,
                special_requirements={"temperature_controlled": False, "stackable": True},
                hazmat=False,
            ),
            Cargo(
                id="cargo_002",
                weight=18000.0,  # 18 tonnes
                value=75000.0,
                special_requirements={"temperature_controlled": True, "min_temp": 2, "max_temp": 8},
                hazmat=False,
            ),
        ]
        db.add_all(cargoes)

        # Create initial cost settings
        cost_settings = CostSettings(
            fuel_price_per_liter=settings.DEFAULT_FUEL_PRICE,
            driver_daily_salary=settings.DEFAULT_DRIVER_SALARY,
            toll_rates=settings.DEFAULT_TOLL_RATES,
            overheads={
                "leasing": 20.0,
                "depreciation": 10.0,
                "insurance": 15.0,
            },
            cargo_factors={
                "cleaning": 10.0,
                "insurance_rate": 0.001,
            },
        )
        db.add(cost_settings)

        db.commit()
        logger.info("Created initial data")


def main() -> None:
    """Initialize the database."""
    logger.info("Creating initial database")
    init_db()
    logger.info("Database created")

    logger.info("Creating initial data")
    create_initial_data()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
