"""Repository for Driver entity."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities.driver import Driver
from src.infrastructure.models import Driver as DriverModel


class DriverRepository:
    """Repository for managing driver persistence."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self._session = session

    def create(self, driver: Driver) -> Driver:
        """Create a new driver."""
        driver_model = DriverModel(
            id=str(driver.id),  # Convert UUID to string
            first_name=driver.first_name,
            last_name=driver.last_name,
            license_number=driver.license_number,
            license_type=driver.license_type,
            license_expiry=driver.license_expiry,
            contact_number=driver.contact_number,
            email=driver.email,
            years_experience=driver.years_experience,
            is_active=driver.is_active,
        )
        self._session.add(driver_model)
        self._session.commit()
        return self._to_domain(driver_model)

    def get_by_id(self, driver_id: UUID) -> Optional[Driver]:
        """Get driver by ID."""
        stmt = select(DriverModel).where(DriverModel.id == str(driver_id))  # Convert UUID to string
        driver_model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(driver_model) if driver_model else None

    def get_all(self) -> List[Driver]:
        """Get all drivers."""
        stmt = select(DriverModel)
        driver_models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(dm) for dm in driver_models]

    def update(self, driver: Driver) -> Optional[Driver]:
        """Update existing driver."""
        stmt = select(DriverModel).where(DriverModel.id == str(driver.id))  # Convert UUID to string
        driver_model = self._session.execute(stmt).scalar_one_or_none()
        if not driver_model:
            return None

        driver_model.first_name = driver.first_name
        driver_model.last_name = driver.last_name
        driver_model.license_number = driver.license_number
        driver_model.license_type = driver.license_type
        driver_model.license_expiry = driver.license_expiry
        driver_model.contact_number = driver.contact_number
        driver_model.email = driver.email
        driver_model.years_experience = driver.years_experience
        driver_model.is_active = driver.is_active

        self._session.commit()
        return self._to_domain(driver_model)

    def delete(self, driver_id: UUID) -> bool:
        """Delete driver by ID."""
        stmt = select(DriverModel).where(DriverModel.id == str(driver_id))  # Convert UUID to string
        driver_model = self._session.execute(stmt).scalar_one_or_none()
        if not driver_model:
            return False

        self._session.delete(driver_model)
        self._session.commit()
        return True

    @staticmethod
    def _to_domain(model: DriverModel) -> Driver:
        """Convert database model to domain entity."""
        return Driver(
            id=UUID(model.id),  # Convert string back to UUID
            first_name=model.first_name,
            last_name=model.last_name,
            license_number=model.license_number,
            license_type=model.license_type,
            license_expiry=model.license_expiry,
            contact_number=model.contact_number,
            email=model.email,
            years_experience=model.years_experience,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
