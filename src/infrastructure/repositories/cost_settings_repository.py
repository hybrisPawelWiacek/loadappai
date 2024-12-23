"""Cost settings repository implementation."""
from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy import desc
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.entities import (
    CostSettings as CostSettingsEntity,
    TransportSettings as TransportSettingsEntity,
    SystemSettings as SystemSettingsEntity,
    CostHistoryEntry as CostHistoryEntryEntity,
)
from src.infrastructure.database import Database
from src.infrastructure.models import (
    CostSettings as CostSettingsModel,
    TransportSettings as TransportSettingsModel,
    SystemSettings as SystemSettingsModel,
    CostHistory as CostHistoryModel,
)
from src.infrastructure.repositories.base import Repository
from src.infrastructure.utils import convert_dict_decimals


class CostSettingsRepository(Repository[CostSettingsEntity]):
    """Repository for managing cost settings and related entities."""

    def __init__(self, db: Database):
        """Initialize repository with database connection."""
        super().__init__(db)

    def create(self, entity: CostSettingsEntity) -> CostSettingsEntity:
        """Create a new entity."""
        return self.create_cost_settings(entity)

    def get(self, id: str) -> Optional[CostSettingsEntity]:
        """Get entity by ID."""
        model = self.db.query(CostSettingsModel).filter_by(id=id).first()
        return self._to_entity(model) if model else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CostSettingsEntity]:
        """Get all entities with pagination."""
        models = self.db.query(CostSettingsModel).offset(skip).limit(limit).all()
        return [self._to_entity(model) for model in models]

    def update(self, id: str, entity: CostSettingsEntity) -> Optional[CostSettingsEntity]:
        """Update an entity."""
        model = self.db.query(CostSettingsModel).filter_by(id=id).first()
        if not model:
            return None
        
        # Update fields
        for key, value in entity.dict().items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, id: str) -> bool:
        """Delete an entity."""
        model = self.db.query(CostSettingsModel).filter_by(id=id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def get_current_cost_settings(self) -> Optional[CostSettingsEntity]:
        """Get current active cost settings."""
        db_settings = (
            self.db.query(CostSettingsModel)
            .filter(CostSettingsModel.is_active == True)
            .order_by(desc(CostSettingsModel.last_modified))
            .first()
        )
        if not db_settings:
            default = CostSettingsEntity.get_default()
            return self.create_cost_settings(default)
        return self._to_entity(db_settings)

    def create_cost_settings(self, entity: CostSettingsEntity) -> CostSettingsEntity:
        """Create new cost settings."""
        # Deactivate current settings
        current = self.db.query(CostSettingsModel).filter_by(is_active=True).first()
        if current:
            current.is_active = False
            self.db.add(current)

        # Create new settings with a new ID
        model = self._to_model(entity)
        model.id = str(uuid4())  # Generate new ID
        model.is_active = True
        model.last_modified = datetime.now(timezone.utc)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update_cost_settings(self, entity: CostSettingsEntity) -> CostSettingsEntity:
        """Update cost settings."""
        # Get current version number
        current = self.db.query(CostSettingsModel).filter_by(is_active=True).first()
        if current:
            current_version = float(current.version)
            new_version = str(current_version + 1.0)
            current.is_active = False
            self.db.add(current)
        else:
            new_version = "1.0"

        # Create new version
        entity.version = new_version
        entity.is_active = True
        entity.last_modified = datetime.now(timezone.utc)

        return self.create_cost_settings(entity)

    def get_cost_settings_by_version(self, version: str) -> Optional[CostSettingsEntity]:
        """Get cost settings by version."""
        db_settings = self.db.query(CostSettingsModel).filter_by(version=version).first()
        return self._to_entity(db_settings) if db_settings else None

    def add_cost_history_entry(self, entry: CostHistoryEntryEntity) -> CostHistoryEntryEntity:
        """Add a new cost history entry."""
        # Convert Decimal values to float and UUID to str for JSON storage
        cost_components = convert_dict_decimals(entry.cost_components)
        settings_snapshot = convert_dict_decimals(entry.settings_snapshot)
        
        db_entry = CostHistoryModel(
            id=str(uuid4()),  # Generate new ID
            route_id=str(entry.route_id),
            calculation_date=entry.calculation_date,
            total_cost=float(entry.total_cost),
            currency=entry.currency,
            calculation_method=entry.calculation_method,
            version=entry.version,
            is_final=entry.is_final,
            cost_components=cost_components,
            settings_snapshot=settings_snapshot
        )
        self.db.add(db_entry)
        self.db.commit()
        self.db.refresh(db_entry)
        return CostHistoryEntryEntity(
            id=UUID(db_entry.id),
            route_id=UUID(db_entry.route_id),
            calculation_date=db_entry.calculation_date,
            total_cost=Decimal(str(db_entry.total_cost)),
            currency=db_entry.currency,
            calculation_method=db_entry.calculation_method,
            version=db_entry.version,
            is_final=db_entry.is_final,
            cost_components={k: Decimal(str(v)) for k, v in db_entry.cost_components.items()},
            settings_snapshot=db_entry.settings_snapshot
        )

    def get_cost_history(self, route_id: UUID) -> List[CostHistoryEntryEntity]:
        """Get cost calculation history for a route."""
        # Convert route_id to string if it's a UUID
        route_id_str = str(route_id)
        history = (
            self.db.query(CostHistoryModel)
            .filter(CostHistoryModel.route_id == route_id_str)
            .order_by(desc(CostHistoryModel.calculation_date))
            .all()
        )
        return [
            CostHistoryEntryEntity(
                id=UUID(entry.id),
                route_id=UUID(entry.route_id),
                calculation_date=entry.calculation_date,
                total_cost=Decimal(str(entry.total_cost)),
                currency=entry.currency,
                calculation_method=entry.calculation_method,
                version=entry.version,
                is_final=entry.is_final,
                cost_components={k: Decimal(str(v)) for k, v in entry.cost_components.items()},
                settings_snapshot=entry.settings_snapshot
            )
            for entry in history
        ]

    def create_transport_settings(self, settings: TransportSettingsEntity) -> TransportSettingsEntity:
        """Create new transport settings."""
        # Deactivate current settings
        current = self.db.query(TransportSettingsModel).filter_by(is_active=True).first()
        if current:
            current.is_active = False
            self.db.add(current)

        # Create new settings with a new ID
        model = TransportSettingsModel(
            id=str(uuid4()),  # Generate new ID
            vehicle_types=settings.vehicle_types,
            equipment_types=settings.equipment_types,
            cargo_types=settings.cargo_types,
            loading_time_minutes=settings.loading_time_minutes,
            unloading_time_minutes=settings.unloading_time_minutes,
            max_driving_hours=settings.max_driving_hours,
            required_rest_hours=settings.required_rest_hours,
            max_working_days=settings.max_working_days,
            speed_limits=settings.speed_limits,
            is_active=True,
            last_modified=datetime.now(timezone.utc)
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return TransportSettingsEntity(
            id=UUID(model.id),
            vehicle_types=model.vehicle_types,
            equipment_types=model.equipment_types,
            cargo_types=model.cargo_types,
            loading_time_minutes=model.loading_time_minutes,
            unloading_time_minutes=model.unloading_time_minutes,
            max_driving_hours=model.max_driving_hours,
            required_rest_hours=model.required_rest_hours,
            max_working_days=model.max_working_days,
            speed_limits=model.speed_limits,
            is_active=model.is_active,
            last_modified=model.last_modified
        )

    def update_transport_settings(self, settings: TransportSettingsEntity) -> TransportSettingsEntity:
        """Update transport settings."""
        # Deactivate current settings
        current = self.db.query(TransportSettingsModel).filter_by(is_active=True).first()
        if current:
            current.is_active = False
            self.db.add(current)

        return self.create_transport_settings(settings)

    def create_system_settings(self, settings: SystemSettingsEntity) -> SystemSettingsEntity:
        """Create new system settings."""
        # Deactivate current settings
        current = self.db.query(SystemSettingsModel).filter_by(is_active=True).first()
        if current:
            current.is_active = False
            self.db.add(current)

        # Create new settings with a new ID
        model = SystemSettingsModel(
            id=str(uuid4()),  # Generate new ID
            api_url=settings.api_url,
            api_version=settings.api_version,
            request_timeout_seconds=settings.request_timeout_seconds,
            default_currency=settings.default_currency,
            default_language=settings.default_language,
            enable_cost_history=settings.enable_cost_history,
            enable_route_optimization=settings.enable_route_optimization,
            enable_real_time_tracking=settings.enable_real_time_tracking,
            maps_provider=settings.maps_provider,
            geocoding_provider=settings.geocoding_provider,
            min_margin_percent=float(settings.min_margin_percent),
            max_margin_percent=float(settings.max_margin_percent),
            price_rounding_decimals=settings.price_rounding_decimals,
            max_route_duration=settings.max_route_duration,
            is_active=True,
            last_modified=datetime.now(timezone.utc)
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return SystemSettingsEntity(
            id=UUID(model.id),
            api_url=model.api_url,
            api_version=model.api_version,
            request_timeout_seconds=model.request_timeout_seconds,
            default_currency=model.default_currency,
            default_language=model.default_language,
            enable_cost_history=model.enable_cost_history,
            enable_route_optimization=model.enable_route_optimization,
            enable_real_time_tracking=model.enable_real_time_tracking,
            maps_provider=model.maps_provider,
            geocoding_provider=model.geocoding_provider,
            min_margin_percent=Decimal(str(model.min_margin_percent)),
            max_margin_percent=Decimal(str(model.max_margin_percent)),
            price_rounding_decimals=model.price_rounding_decimals,
            max_route_duration=model.max_route_duration,
            is_active=model.is_active,
            last_modified=model.last_modified
        )

    def update_system_settings(self, settings: SystemSettingsEntity) -> SystemSettingsEntity:
        """Update system settings."""
        # Deactivate current settings
        current = self.db.query(SystemSettingsModel).filter_by(is_active=True).first()
        if current:
            current.is_active = False
            self.db.add(current)

        return self.create_system_settings(settings)

    def _to_model(self, entity: CostSettingsEntity) -> CostSettingsModel:
        """Convert entity to model."""
        return CostSettingsModel(
            id=str(entity.id),
            fuel_prices={k: float(v) for k, v in entity.fuel_prices.items()},
            toll_rates={k: {"highway": float(v["highway"]), "national": float(v["national"])} for k, v in entity.toll_rates.items()},
            driver_rates={k: float(v) for k, v in entity.driver_rates.items()},
            rest_period_rate=float(entity.rest_period_rate),
            loading_unloading_rate=float(entity.loading_unloading_rate),
            maintenance_rate_per_km=float(entity.maintenance_rate_per_km),
            empty_driving_factors={k: float(v) for k, v in entity.empty_driving_factors.items()},
            cargo_factors={k: {sk: float(sv) for sk, sv in v.items()} for k, v in entity.cargo_factors.items()},
            overhead_rates={k: float(v) for k, v in entity.overhead_rates.items()},
            version=entity.version,
            is_active=entity.is_active,
            last_modified=entity.last_modified,
            extra_data=entity.extra_data
        )

    def _to_entity(self, model: CostSettingsModel) -> CostSettingsEntity:
        """Convert model to entity."""
        # Convert toll rates, handling both old and new formats
        toll_rates = {}
        for k, v in model.toll_rates.items():
            if isinstance(v, (float, int, str, Decimal)):
                # Old format - convert to new format with highway rate = old rate, national rate = 70% of highway
                highway_rate = Decimal(str(v))
                toll_rates[k] = {
                    "highway": highway_rate,
                    "national": highway_rate * Decimal("0.7")
                }
            else:
                # New format - already has highway and national rates
                toll_rates[k] = {
                    "highway": Decimal(str(v["highway"])),
                    "national": Decimal(str(v["national"]))
                }
        
        return CostSettingsEntity(
            id=UUID(model.id),
            fuel_prices={k: Decimal(str(v)) for k, v in model.fuel_prices.items()},
            toll_rates=toll_rates,
            driver_rates={k: Decimal(str(v)) for k, v in model.driver_rates.items()},
            rest_period_rate=Decimal(str(model.rest_period_rate)),
            loading_unloading_rate=Decimal(str(model.loading_unloading_rate)),
            maintenance_rate_per_km=Decimal(str(model.maintenance_rate_per_km)),
            empty_driving_factors={k: Decimal(str(v)) for k, v in model.empty_driving_factors.items()},
            cargo_factors={k: {sk: Decimal(str(sv)) for sk, sv in v.items()} for k, v in model.cargo_factors.items()},
            overhead_rates={k: Decimal(str(v)) for k, v in model.overhead_rates.items()},
            version=model.version,
            is_active=model.is_active,
            last_modified=model.last_modified,
            extra_data=model.extra_data
        )

    def get_default(self) -> CostSettingsEntity:
        """Get default cost settings."""
        return CostSettingsEntity(
            id=uuid4(),
            fuel_prices={
                "PL": Decimal("1.50"),
                "DE": Decimal("1.80"),
            },
            toll_rates={
                "PL": {"highway": Decimal("0.15"), "national": Decimal("0.10")},
                "DE": {"highway": Decimal("0.25"), "national": Decimal("0.20")},
            },
            driver_rates={
                "PL": Decimal("25.00"),
                "DE": Decimal("35.00"),
            },
            rest_period_rate=Decimal("20.00"),
            loading_unloading_rate=Decimal("30.00"),
            maintenance_rate_per_km=Decimal("0.10"),
            empty_driving_factors={
                "fuel": Decimal("0.8"),
                "toll": Decimal("1.0"),
                "driver": Decimal("1.0"),
            },
            cargo_factors={
                "standard": {
                    "weight": Decimal("1.0"),
                    "volume": Decimal("1.0"),
                },
                "refrigerated": {
                    "weight": Decimal("1.2"),
                    "volume": Decimal("1.1"),
                    "temperature": Decimal("1.3"),
                },
            },
            overhead_rates={
                "distance": Decimal("0.05"),
                "time": Decimal("10.00"),
                "fixed": Decimal("100.00"),
            },
            version="1.0",
            is_active=True,
            last_modified=datetime.now(timezone.utc),
        )
