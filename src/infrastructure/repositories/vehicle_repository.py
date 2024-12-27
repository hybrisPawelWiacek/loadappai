"""Repository for Vehicle entity."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from src.domain.entities.vehicle import Vehicle, VehicleSpecification
from src.domain.interfaces.repositories.vehicle_repository import VehicleRepository as VehicleRepositoryInterface
from src.infrastructure.database import Database
from src.infrastructure.models import Vehicle as VehicleModel


class VehicleRepository(VehicleRepositoryInterface):
    """Repository for managing vehicle persistence."""

    def __init__(self, db: Database):
        """Initialize repository with database session."""
        self.db = db
        self._session = db.session

    def create(self, vehicle: Vehicle) -> Vehicle:
        """Create a new vehicle."""
        vehicle_model = VehicleModel(
            id=str(vehicle.id),
            vehicle_type=vehicle.specifications.vehicle_type,
            fuel_consumption_rate=vehicle.specifications.fuel_consumption_rate,
            empty_consumption_factor=vehicle.specifications.empty_consumption_factor,
            maintenance_rate_per_km=float(vehicle.specifications.maintenance_rate_per_km),
            toll_class=vehicle.specifications.toll_class,
            has_special_equipment=vehicle.specifications.has_special_equipment,
            equipment_costs=vehicle.specifications.equipment_costs,
        )
        self._session.add(vehicle_model)
        self._session.commit()
        return self._to_domain(vehicle_model)

    def get(self, id: UUID) -> Optional[Vehicle]:
        """Get vehicle by ID."""
        stmt = select(VehicleModel).where(VehicleModel.id == str(id))
        vehicle_model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(vehicle_model) if vehicle_model else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get all vehicles."""
        stmt = select(VehicleModel).offset(skip).limit(limit)
        vehicle_models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(vm) for vm in vehicle_models]

    def update(self, id: UUID, vehicle: Vehicle) -> Optional[Vehicle]:
        """Update existing vehicle."""
        stmt = select(VehicleModel).where(VehicleModel.id == str(id))
        vehicle_model = self._session.execute(stmt).scalar_one_or_none()
        if not vehicle_model:
            return None

        vehicle_model.vehicle_type = vehicle.specifications.vehicle_type
        vehicle_model.fuel_consumption_rate = vehicle.specifications.fuel_consumption_rate
        vehicle_model.empty_consumption_factor = vehicle.specifications.empty_consumption_factor
        vehicle_model.maintenance_rate_per_km = float(vehicle.specifications.maintenance_rate_per_km)
        vehicle_model.toll_class = vehicle.specifications.toll_class
        vehicle_model.has_special_equipment = vehicle.specifications.has_special_equipment
        vehicle_model.equipment_costs = vehicle.specifications.equipment_costs

        self._session.commit()
        return self._to_domain(vehicle_model)

    def delete(self, id: UUID) -> bool:
        """Delete vehicle by ID."""
        stmt = select(VehicleModel).where(VehicleModel.id == str(id))
        vehicle_model = self._session.execute(stmt).scalar_one_or_none()
        if not vehicle_model:
            return False

        self._session.delete(vehicle_model)
        self._session.commit()
        return True

    def count(self) -> int:
        """Get total count of vehicles."""
        return self._session.query(VehicleModel).count()

    def get_by_type(self, vehicle_type: str) -> List[Vehicle]:
        """Get all vehicles of a specific type."""
        stmt = select(VehicleModel).where(VehicleModel.vehicle_type == vehicle_type)
        vehicle_models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(vm) for vm in vehicle_models]

    def get_active(self) -> List[Vehicle]:
        """Get all active vehicles."""
        stmt = select(VehicleModel).where(VehicleModel.is_active == True)
        vehicle_models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(vm) for vm in vehicle_models]

    @staticmethod
    def _to_domain(model: VehicleModel) -> Vehicle:
        """Convert database model to domain entity."""
        specs = VehicleSpecification(
            vehicle_type=model.vehicle_type,
            fuel_consumption_rate=model.fuel_consumption_rate,
            empty_consumption_factor=model.empty_consumption_factor,
            maintenance_rate_per_km=model.maintenance_rate_per_km,
            toll_class=model.toll_class,
            has_special_equipment=model.has_special_equipment,
            equipment_costs=model.equipment_costs
        )
        return Vehicle(id=UUID(model.id), specifications=specs)
