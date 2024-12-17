"""Cost settings repository implementation."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.domain.entities import CostSettings as CostSettingsEntity
from src.infrastructure.models import CostSettings as CostSettingsModel
from src.infrastructure.repositories.base import Repository


class CostSettingsRepository(Repository[CostSettingsEntity]):
    """Repository for managing cost settings entities."""

    def create(self, entity: CostSettingsEntity) -> CostSettingsEntity:
        """Create new cost settings."""
        db_settings = CostSettingsModel(
            id=str(entity.id),
            fuel_price_per_liter=float(entity.fuel_price_per_liter),
            driver_daily_salary=float(entity.driver_daily_salary),
            toll_rates={k: str(v) for k, v in entity.toll_rates.items()},
            overheads={k: str(v) for k, v in entity.overheads.items()},
            cargo_factors={k: str(v) for k, v in entity.cargo_factors.items()},
            last_modified=entity.last_modified.astimezone(timezone.utc),
            extra_data=entity.metadata if entity.metadata else None,
        )
        self.db.add(db_settings)
        self.db.commit()
        self.db.refresh(db_settings)
        return self._to_entity(db_settings)

    def get(self, id: str) -> Optional[CostSettingsEntity]:
        """Get cost settings by ID."""
        db_settings = self.db.query(CostSettingsModel).filter(CostSettingsModel.id == id).first()
        return self._to_entity(db_settings) if db_settings else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CostSettingsEntity]:
        """Get all cost settings with pagination."""
        db_settings = self.db.query(CostSettingsModel).offset(skip).limit(limit).all()
        return [self._to_entity(settings) for settings in db_settings]

    def update(self, id: str, entity: CostSettingsEntity) -> Optional[CostSettingsEntity]:
        """Update cost settings."""
        db_settings = self.db.query(CostSettingsModel).filter(CostSettingsModel.id == id).first()
        if not db_settings:
            return None

        update_data = {
            "fuel_price_per_liter": float(entity.fuel_price_per_liter),
            "driver_daily_salary": float(entity.driver_daily_salary),
            "toll_rates": {k: str(v) for k, v in entity.toll_rates.items()},
            "overheads": {k: str(v) for k, v in entity.overheads.items()},
            "cargo_factors": {k: str(v) for k, v in entity.cargo_factors.items()},
            "last_modified": entity.last_modified.astimezone(timezone.utc),
            "extra_data": entity.metadata if entity.metadata else None,
        }

        for key, value in update_data.items():
            setattr(db_settings, key, value)

        self.db.commit()
        self.db.refresh(db_settings)
        return self._to_entity(db_settings)

    def delete(self, id: str) -> bool:
        """Delete cost settings."""
        db_settings = self.db.query(CostSettingsModel).filter(CostSettingsModel.id == id).first()
        if not db_settings:
            return False

        self.db.delete(db_settings)
        self.db.commit()
        return True

    def get_latest(self) -> Optional[CostSettingsEntity]:
        """Get the most recent cost settings."""
        db_settings = (
            self.db.query(CostSettingsModel)
            .order_by(CostSettingsModel.last_modified.desc())
            .first()
        )
        return self._to_entity(db_settings) if db_settings else None

    def get_by_date(self, date: datetime) -> Optional[CostSettingsEntity]:
        """Get cost settings valid at a specific date."""
        db_settings = (
            self.db.query(CostSettingsModel)
            .filter(CostSettingsModel.last_modified <= date.astimezone(timezone.utc))
            .order_by(CostSettingsModel.last_modified.desc())
            .first()
        )
        return self._to_entity(db_settings) if db_settings else None

    def _to_entity(self, db_settings: CostSettingsModel) -> Optional[CostSettingsEntity]:
        """Convert database model to domain entity."""
        if not db_settings:
            return None

        return CostSettingsEntity(
            id=db_settings.id,
            fuel_price_per_liter=Decimal(str(db_settings.fuel_price_per_liter)),
            driver_daily_salary=Decimal(str(db_settings.driver_daily_salary)),
            toll_rates={k: Decimal(v) for k, v in db_settings.toll_rates.items()},
            overheads={k: Decimal(v) for k, v in db_settings.overheads.items()},
            cargo_factors={k: Decimal(v) for k, v in db_settings.cargo_factors.items()},
            last_modified=db_settings.last_modified.replace(tzinfo=timezone.utc),
            metadata=db_settings.extra_data,
        )
