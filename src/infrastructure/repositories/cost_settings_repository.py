"""Cost settings repository implementation."""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import warnings
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.entities.cost import CostSettings, CostHistoryEntry, CostSettingsVersion
from src.domain.entities.vehicle import TransportSettings, SystemSettings
from src.domain.interfaces.repositories.cost_settings_repository import CostSettingsRepository as CostSettingsRepositoryInterface
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError
from src.infrastructure.models import (
    CostSettings as CostSettingsModel,
    CostHistory as CostHistoryModel,
    TransportSettings as TransportSettingsModel,
    SystemSettings as SystemSettingsModel
)
from src.infrastructure.logging import get_logger

logger = get_logger()

def convert_dict_decimals(d: Dict) -> Dict:
    """Convert Decimal values in dictionary to float for JSON storage."""
    if not d:
        return {}
    result = {}
    for k, v in d.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, dict):
            result[k] = convert_dict_decimals(v)
        else:
            result[k] = v
    return result

class CostSettingsRepository(CostSettingsRepositoryInterface):
    """Repository implementation for cost settings."""

    def __init__(self, db):
        """Initialize repository with database."""
        self.db = db

    def get_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
        """Get cost settings for a route.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            CostSettings if found, None otherwise
        """
        try:
            with self.db.session() as session:
                model = (
                    session.query(CostSettingsModel)
                    .filter_by(route_id=str(route_id))
                    .order_by(desc(CostSettingsModel.version))
                    .first()
                )
                return self._to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error getting settings for route {route_id}: {e}")
            return None

    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings.
        
        Args:
            settings: CostSettings to save
            
        Returns:
            Saved CostSettings with updated metadata
            
        Raises:
            ValueError: If settings are invalid
        """
        try:
            with self.db.session() as session:
                # Convert entity to model
                model = CostSettingsModel(
                    id=str(settings.id) if settings.id else str(uuid4()),
                    route_id=str(settings.route_id),
                    version=settings.version.value,
                    fuel_rates=convert_dict_decimals(settings.fuel_rates),
                    toll_rates=convert_dict_decimals(settings.toll_rates),
                    driver_rates=convert_dict_decimals(settings.driver_rates),
                    overhead_rates=convert_dict_decimals(settings.overhead_rates),
                    maintenance_rates=convert_dict_decimals(settings.maintenance_rates),
                    enabled_components=list(settings.enabled_components),
                    created_at=settings.created_at or datetime.utcnow(),
                    modified_at=datetime.utcnow(),
                    created_by=settings.created_by,
                    modified_by=settings.modified_by
                )
                
                # Save to database
                session.add(model)
                session.commit()
                session.refresh(model)
                
                return self._to_entity(model)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def get_history(self, route_id: UUID) -> List[CostSettings]:
        """Get history of cost settings for a route.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            List of CostSettings ordered by version
        """
        try:
            with self.db.session() as session:
                models = (
                    session.query(CostSettingsModel)
                    .filter_by(route_id=str(route_id))
                    .order_by(desc(CostSettingsModel.version))
                    .all()
                )
                return [self._to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting history for route {route_id}: {e}")
            return []

    def get_by_version(self, route_id: UUID, version: CostSettingsVersion) -> Optional[CostSettings]:
        """Get specific version of cost settings.
        
        Args:
            route_id: UUID of the route
            version: Version to retrieve
            
        Returns:
            CostSettings if found, None otherwise
        """
        try:
            with self.db.session() as session:
                model = (
                    session.query(CostSettingsModel)
                    .filter_by(route_id=str(route_id), version=version.value)
                    .first()
                )
                return self._to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error getting version {version} for route {route_id}: {e}")
            return None

    def get_current(self, route_id: UUID) -> Optional[CostSettings]:
        """Get current version of cost settings.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            Current CostSettings if found, None otherwise
        """
        return self.get_by_route_id(route_id)

    def count(self, route_id: UUID) -> int:
        """Count number of versions for a route.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            Number of versions
        """
        try:
            with self.db.session() as session:
                return (
                    session.query(CostSettingsModel)
                    .filter_by(route_id=str(route_id))
                    .count()
                )
        except Exception as e:
            logger.error(f"Error counting versions for route {route_id}: {e}")
            return 0

    def _to_entity(self, model: CostSettingsModel) -> CostSettings:
        """Convert model to domain entity."""
        if not model:
            return None
        return CostSettings(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            version=CostSettingsVersion(model.version),
            fuel_rates=model.fuel_rates,
            toll_rates=model.toll_rates,
            driver_rates=model.driver_rates,
            overhead_rates=model.overhead_rates,
            maintenance_rates=model.maintenance_rates,
            enabled_components=set(model.enabled_components),
            created_at=model.created_at,
            modified_at=model.modified_at,
            created_by=model.created_by,
            modified_by=model.modified_by
        )

    def get_defaults(self, route_id: UUID = None) -> CostSettings:
        """Get default cost settings.
        
        Args:
            route_id: Optional route ID for defaults
            
        Returns:
            Default CostSettings configuration
        """
        return CostSettings.get_default(route_id or uuid4())

    def get_version(self, version: str) -> Optional[CostSettings]:
        """Get settings by version."""
        if not version:
            raise ValidationError("Version cannot be empty")
            
        try:
            with self.db.session() as session:
                model = (
                    session.query(CostSettingsModel)
                    .filter_by(version=version)
                    .first()
                )
                return self._to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error getting settings version {version}: {e}")
            raise

    def validate(self, settings: CostSettings) -> bool:
        """Validate settings configuration."""
        try:
            # Basic validation
            if not settings:
                raise ValidationError("Settings cannot be None")
                
            # Check required fields
            if not settings.enabled_components:
                raise ValidationError("At least one cost component must be enabled")
                
            # Validate rates
            if "fuel" in settings.enabled_components and not settings.fuel_rates:
                raise ValidationError("Fuel rates required when fuel component enabled")
                
            if "toll" in settings.enabled_components and not settings.toll_rates:
                raise ValidationError("Toll rates required when toll component enabled")
                
            if "driver" in settings.enabled_components and not settings.driver_rates:
                raise ValidationError("Driver rates required when driver component enabled")
                
            # Validate version format
            if not isinstance(settings.version, CostSettingsVersion):
                raise ValidationError("Invalid version format")
                
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating settings: {e}")
            raise ValidationError(str(e))

    def create_cost_settings(self, entity: CostSettings) -> CostSettings:
        """Create new cost settings."""
        # Deactivate current settings
        with self.db.session() as session:
            current = session.query(CostSettingsModel).filter_by(is_active=True).first()
            if current:
                current.is_active = False
                session.add(current)

            # Create new settings with a new ID
            model = self._to_model(entity)
            model.id = str(uuid4())  # Generate new ID
            model.is_active = True
            model.last_modified = datetime.now()
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def update_cost_settings(self, entity: CostSettings) -> CostSettings:
        """Update cost settings."""
        # Get current version number
        with self.db.session() as session:
            current = session.query(CostSettingsModel).filter_by(is_active=True).first()
            if current:
                current_version = float(current.version)
                new_version = str(current_version + 1.0)
                current.is_active = False
                session.add(current)
            else:
                new_version = "1.0"

            # Create new version
            entity.version = new_version
            entity.is_active = True
            entity.last_modified = datetime.now()

            return self.create_cost_settings(entity)

    def get_cost_settings_by_version(self, version: str) -> Optional[CostSettings]:
        """Get cost settings by version."""
        with self.db.session() as session:
            db_settings = session.query(CostSettingsModel).filter_by(version=version).first()
            return self._to_entity(db_settings) if db_settings else None

    def add_cost_history_entry(self, entry: CostHistoryEntry) -> CostHistoryEntry:
        """Add a new cost history entry."""
        # Convert Decimal values to float and UUID to str for JSON storage
        cost_components = convert_dict_decimals(entry.cost_components)
        settings_snapshot = convert_dict_decimals(entry.settings_snapshot)
        
        with self.db.session() as session:
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
            session.add(db_entry)
            session.commit()
            session.refresh(db_entry)
            return CostHistoryEntry(
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

    def get_cost_history(self, route_id: UUID) -> List[CostHistoryEntry]:
        """Get cost calculation history for a route."""
        # Convert route_id to string if it's a UUID
        route_id_str = str(route_id)
        with self.db.session() as session:
            history = (
                session.query(CostHistoryModel)
                .filter(CostHistoryModel.route_id == route_id_str)
                .order_by(desc(CostHistoryModel.calculation_date))
                .all()
            )
            return [
                CostHistoryEntry(
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

    def create_transport_settings(self, settings: TransportSettings) -> TransportSettings:
        """Create new transport settings."""
        # Deactivate current settings
        with self.db.session() as session:
            current = session.query(TransportSettingsModel).filter_by(is_active=True).first()
            if current:
                current.is_active = False
                session.add(current)

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
                last_modified=datetime.now()
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return TransportSettings(
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

    def update_transport_settings(self, settings: TransportSettings) -> TransportSettings:
        """Update transport settings."""
        # Deactivate current settings
        with self.db.session() as session:
            current = session.query(TransportSettingsModel).filter_by(is_active=True).first()
            if current:
                current.is_active = False
                session.add(current)

            return self.create_transport_settings(settings)

    def create_system_settings(self, settings: SystemSettings) -> SystemSettings:
        """Create new system settings."""
        # Deactivate current settings
        with self.db.session() as session:
            current = session.query(SystemSettingsModel).filter_by(is_active=True).first()
            if current:
                current.is_active = False
                session.add(current)

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
                last_modified=datetime.now()
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return SystemSettings(
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

    def update_system_settings(self, settings: SystemSettings) -> SystemSettings:
        """Update system settings."""
        # Deactivate current settings
        with self.db.session() as session:
            current = session.query(SystemSettingsModel).filter_by(is_active=True).first()
            if current:
                current.is_active = False
                session.add(current)

            return self.create_system_settings(settings)

    # Legacy methods marked as deprecated

    def create(self, entity: CostSettings) -> CostSettings:
        """Create a new entity (DEPRECATED).
        
        Use save() instead.
        """
        warnings.warn(
            "create() is deprecated. Use save() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.save(entity)

    def get(self, id: str) -> Optional[CostSettings]:
        """Get entity by ID (DEPRECATED).
        
        Use get_by_route_id() instead.
        """
        warnings.warn(
            "get() is deprecated. Use get_by_route_id() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_by_route_id(UUID(id))

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CostSettings]:
        """Get all entities with pagination (DEPRECATED)."""
        warnings.warn(
            "get_all() is deprecated and will be removed.",
            DeprecationWarning,
            stacklevel=2
        )
        with self.db.session() as session:
            models = session.query(CostSettingsModel).offset(skip).limit(limit).all()
            return [self._to_entity(model) for model in models]

    def update(self, id: str, entity: CostSettings) -> Optional[CostSettings]:
        """Update an entity (DEPRECATED).
        
        Use save() instead.
        """
        warnings.warn(
            "update() is deprecated. Use save() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.save(entity)

    def delete(self, id: str) -> bool:
        """Delete an entity (DEPRECATED)."""
        warnings.warn(
            "delete() is deprecated and will be removed.",
            DeprecationWarning,
            stacklevel=2
        )
        with self.db.session() as session:
            model = session.query(CostSettingsModel).filter_by(id=id).first()
            if not model:
                return False
            session.delete(model)
            session.commit()
            return True

    def get_current_cost_settings(self) -> Optional[CostSettings]:
        """Get current active cost settings (DEPRECATED).
        
        Use get_defaults() instead.
        """
        warnings.warn(
            "get_current_cost_settings() is deprecated. Use get_defaults() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_defaults()

    def _to_model(self, entity: CostSettings) -> CostSettingsModel:
        """Convert domain entity to database model."""
        return CostSettingsModel(
            id=str(entity.id),
            route_id=str(entity.route_id),
            fuel_rates=convert_dict_decimals(entity.fuel_rates),
            toll_rates=convert_dict_decimals(entity.toll_rates),
            driver_rates=convert_dict_decimals(entity.driver_rates),
            overhead_rates=convert_dict_decimals(entity.overhead_rates),
            maintenance_rates=convert_dict_decimals(entity.maintenance_rates),
            enabled_components=list(entity.enabled_components),
            version=entity.version.value,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
            created_at=entity.created_at or datetime.now(),
            modified_at=entity.modified_at or datetime.now()
        )
