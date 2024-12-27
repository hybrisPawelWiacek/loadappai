"""Cost repository implementation."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.domain.entities.cost import Cost as CostEntity, CostBreakdown
from src.domain.interfaces.repositories.cost_repository import CostRepository as CostRepositoryInterface
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError
from src.infrastructure.database import Database
from src.infrastructure.logging import get_logger
from src.infrastructure.models import Cost as CostModel


def _serialize_uuid(obj: dict) -> dict:
    """Convert UUID objects to strings in a dictionary."""
    if not isinstance(obj, dict):
        return obj
        
    result = {}
    for key, value in obj.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = _serialize_uuid(value)
        elif isinstance(value, list):
            result[key] = [_serialize_uuid(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result


def _serialize_decimal(obj: dict) -> dict:
    """Convert Decimal objects to floats in a dictionary."""
    if not isinstance(obj, dict):
        return obj
        
    result = {}
    for key, value in obj.items():
        if hasattr(value, 'as_integer_ratio'):  # Check if it's a Decimal
            result[key] = float(value)
        elif isinstance(value, dict):
            result[key] = _serialize_decimal(value)
        elif isinstance(value, list):
            result[key] = [_serialize_decimal(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result


def _serialize_breakdown(breakdown: CostBreakdown) -> dict:
    """Convert CostBreakdown to a serializable dictionary."""
    if not breakdown:
        return {}
        
    breakdown_dict = breakdown.model_dump()
    serialized = _serialize_uuid(breakdown_dict)
    return _serialize_decimal(serialized)


def _validate_breakdown(breakdown: dict, route_id: UUID) -> dict:
    """Validate and convert breakdown dictionary to proper format."""
    try:
        if not isinstance(breakdown, dict):
            raise ValidationError("Breakdown must be a dictionary")
            
        # Ensure required fields exist with default empty dictionaries
        required_fields = ['fuel_costs', 'toll_costs', 'driver_costs', 'maintenance_costs']
        for field in required_fields:
            if field not in breakdown:
                breakdown[field] = {}
            
        # Validate that all values in the cost dictionaries are valid Decimals
        for field in required_fields:
            costs = breakdown[field]
            if not isinstance(costs, dict):
                raise ValidationError(f"{field} must be a dictionary")
            try:
                validated_costs = {}
                for key, value in costs.items():
                    try:
                        validated_costs[key] = float(value)  # This will raise ValueError if value is not numeric
                    except (TypeError, ValueError):
                        raise ValidationError(f"Invalid value in {field}.{key}: {value} is not a valid decimal")
                breakdown[field] = validated_costs
            except ValidationError:
                raise  # Re-raise validation errors
            except Exception as e:
                raise ValidationError(f"Invalid value in {field}: {str(e)}")
                
        # Add route_id to breakdown
        breakdown['route_id'] = str(route_id)
                
        # Convert any Decimal values to float
        return _serialize_decimal(breakdown)
    except ValidationError:
        raise  # Re-raise validation errors
    except Exception as e:
        raise ValidationError(f"Invalid breakdown format: {str(e)}")


class CostRepository(CostRepositoryInterface):
    """Repository for managing cost entities."""

    def __init__(self, db: Database):
        """Initialize repository with database connection."""
        self.db = db
        self.model = CostModel

    def create(self, entity: CostEntity) -> CostEntity:
        """Create a new cost entity."""
        with self.db.session() as session:
            model = CostModel(
                id=str(entity.id),
                route_id=str(entity.route_id),
                calculation_date=entity.calculated_at,
                total_cost=float(entity.total_cost),
                currency=entity.metadata.get("currency", "EUR") if entity.metadata else "EUR",
                calculation_method=entity.calculation_method,
                version=entity.version,
                is_final=entity.is_final,
                cost_components=_serialize_breakdown(entity.breakdown),
                settings_snapshot=_serialize_uuid(entity.metadata) if entity.metadata else {}
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def get(self, id: UUID) -> Optional[CostEntity]:
        """Get cost entity by ID."""
        with self.db.session() as session:
            model = session.query(CostModel).filter_by(id=str(id)).first()
            return self._to_entity(model) if model else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CostEntity]:
        """Get all cost entities with pagination."""
        with self.db.session() as session:
            models = session.query(CostModel).offset(skip).limit(limit).all()
            return [self._to_entity(model) for model in models]

    def update(self, id: UUID, entity: CostEntity) -> Optional[CostEntity]:
        """Update a cost entity."""
        with self.db.session() as session:
            model = session.query(CostModel).filter_by(id=str(id)).first()
            if not model:
                return None
            
            # Update fields
            model.total_cost = float(entity.total_cost)
            model.currency = entity.metadata.get("currency", "EUR") if entity.metadata else "EUR"
            model.calculation_method = entity.calculation_method
            model.version = entity.version
            model.is_final = entity.is_final
            model.cost_components = _serialize_breakdown(entity.breakdown)
            model.settings_snapshot = _serialize_uuid(entity.metadata) if entity.metadata else {}
            
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def delete(self, id: UUID) -> bool:
        """Delete a cost entity."""
        with self.db.session() as session:
            model = session.query(CostModel).filter_by(id=str(id)).first()
            if not model:
                return False
            session.delete(model)
            session.commit()
            return True

    def get_by_route_id(self, route_id: UUID) -> List[CostEntity]:
        """Get all costs for a route."""
        with self.db.session() as session:
            models = (
                session.query(CostModel)
                .filter_by(route_id=str(route_id))
                .order_by(desc(CostModel.calculation_date))
                .all()
            )
            if not models:
                raise EntityNotFoundError(f"No costs found for route {route_id}")
            return [self._to_entity(model) for model in models]

    def get_latest_for_route(self, route_id: UUID) -> Optional[CostEntity]:
        """Get latest cost calculation for a route."""
        with self.db.session() as session:
            model = (
                session.query(CostModel)
                .filter_by(route_id=str(route_id))
                .order_by(desc(CostModel.calculation_date))
                .first()
            )
            if not model:
                return None
            return self._to_entity(model)

    def save_with_breakdown(self, entity: CostEntity, breakdown: Dict) -> CostEntity:
        """Save cost with breakdown."""
        try:
            if not isinstance(breakdown, dict):
                raise ValidationError("Invalid breakdown format: must be a dictionary")

            # Add route_id to breakdown if not present
            if 'route_id' not in breakdown:
                breakdown['route_id'] = entity.route_id
            
            # Validate breakdown
            try:
                self._validate_breakdown(breakdown)
            except ValidationError as e:
                raise ValidationError(f"Invalid breakdown data: {str(e)}")
            
            # Calculate total cost from components
            total_cost = Decimal('0')
            cost_fields = ['fuel_costs', 'toll_costs', 'driver_costs', 'maintenance_costs']
            for field in cost_fields:
                costs = breakdown.get(field, {})
                if isinstance(costs, dict):
                    total_cost += sum(Decimal(str(amount)) for amount in costs.values())
            
            # Convert all Decimal values to float for JSON serialization
            for field in cost_fields:
                costs = breakdown.get(field, {})
                if isinstance(costs, dict):
                    breakdown[field] = {k: float(Decimal(str(v))) for k, v in costs.items()}
            
            try:
                # Create CostBreakdown object and update entity
                breakdown_obj = CostBreakdown(**breakdown)
                entity.breakdown = breakdown_obj
                
                # Update total cost on the entity
                entity.total_cost = float(total_cost)
                
                # Convert entity to model for database
                model = self._to_model(entity)
                
                # Convert breakdown to JSON-serializable format
                if hasattr(model, 'cost_components'):
                    model.cost_components = {
                        'route_id': str(breakdown_obj.route_id),
                        'fuel_costs': {k: float(v) for k, v in breakdown_obj.fuel_costs.items()},
                        'toll_costs': {k: float(v) for k, v in breakdown_obj.toll_costs.items()},
                        'driver_costs': {k: float(v) for k, v in breakdown_obj.driver_costs.items()},
                        'maintenance_costs': {k: float(v) for k, v in breakdown_obj.maintenance_costs.items()},
                        'total_cost': float(total_cost)
                    }
                
                # Ensure total_cost is set on the model
                model.total_cost = float(total_cost)
                
                # Save to database
                with self.db.session() as session:
                    session.add(model)
                    session.commit()
                    session.refresh(model)
                    return self._to_entity(model)
                
            except ValidationError as e:
                raise ValidationError(f"Invalid breakdown data: {str(e)}")
            
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Failed to save cost with breakdown: {str(e)}")

    def get_cost_history(self, cost_id: UUID) -> List[CostEntity]:
        """Get history of changes for a cost calculation."""
        with self.db.session() as session:
            models = (
                session.query(CostModel)
                .filter_by(id=str(cost_id))
                .order_by(desc(CostModel.calculation_date))
                .all()
            )
            if not models:
                raise EntityNotFoundError(f"No history found for cost {cost_id}")
            return [self._to_entity(model) for model in models]

    def count(self) -> int:
        """Get total count of cost records."""
        with self.db.session() as session:
            return session.query(CostModel).count()

    def _to_entity(self, model: CostModel) -> CostEntity:
        """Convert database model to domain entity."""
        if not model:
            return None

        # Get cost components from model
        breakdown_dict = model.cost_components or {}
        
        # Use the stored total_cost from the model
        total_cost = breakdown_dict.get('total_cost', 0)
        
        # Add route_id to breakdown
        breakdown_dict['route_id'] = UUID(model.route_id)  
        
        # Create CostBreakdown with the new dictionary-based structure
        breakdown = CostBreakdown(
            route_id=UUID(model.route_id),
            fuel_costs=breakdown_dict.get('fuel_costs', {}),
            toll_costs=breakdown_dict.get('toll_costs', {}),
            driver_costs=breakdown_dict.get('driver_costs', {}),
            maintenance_costs=breakdown_dict.get('maintenance_costs', {}),
            rest_period_costs=breakdown_dict.get('rest_period_costs', 0),
            loading_unloading_costs=breakdown_dict.get('loading_unloading_costs', 0),
            empty_driving_costs=breakdown_dict.get('empty_driving_costs', {}),
            cargo_specific_costs=breakdown_dict.get('cargo_specific_costs', {}),
            overheads=breakdown_dict.get('overheads', {}),
            total_cost=Decimal(str(total_cost))
        )
        
        return CostEntity(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            breakdown=breakdown,
            calculated_at=model.calculation_date,
            metadata=model.settings_snapshot,
            version=model.version,
            is_final=model.is_final,
            calculation_method=model.calculation_method,
            total_cost=float(model.total_cost)
        )

    def _to_model(self, entity: CostEntity) -> CostModel:
        """Convert domain entity to database model."""
        if not entity:
            return None
        
        # Use the total_cost from the entity's breakdown
        total_cost = float(entity.breakdown.total_cost) if entity.breakdown else 0
        
        # Create cost components dictionary with total from breakdown
        cost_components = {
            'fuel_costs': entity.breakdown.fuel_costs,
            'toll_costs': entity.breakdown.toll_costs,
            'driver_costs': entity.breakdown.driver_costs,
            'maintenance_costs': entity.breakdown.maintenance_costs,
            'rest_period_costs': entity.breakdown.rest_period_costs,
            'loading_unloading_costs': entity.breakdown.loading_unloading_costs,
            'empty_driving_costs': entity.breakdown.empty_driving_costs,
            'cargo_specific_costs': entity.breakdown.cargo_specific_costs,
            'overheads': entity.breakdown.overheads,
            'total_cost': total_cost
        }

        return CostModel(
            id=str(entity.id),
            route_id=str(entity.route_id),
            cost_components=cost_components,
            calculation_date=entity.calculated_at,
            settings_snapshot=entity.metadata,
            version=entity.version,
            is_final=entity.is_final,
            calculation_method=entity.calculation_method,
            total_cost=float(entity.total_cost)
        )

    def _validate_breakdown(self, breakdown: Dict) -> None:
        """Validate cost breakdown structure."""
        if not isinstance(breakdown, dict):
            raise ValidationError("Invalid breakdown format: must be a dictionary")

        # Validate route_id is present
        if 'route_id' not in breakdown:
            raise ValidationError("Invalid breakdown format: missing required field 'route_id'")

        # Validate cost fields
        required_fields = ['fuel_costs', 'toll_costs', 'driver_costs', 'maintenance_costs']
        for field in required_fields:
            if field not in breakdown:
                breakdown[field] = {}  # Initialize empty dict for missing fields
            
            costs = breakdown.get(field, {})
            if not isinstance(costs, dict):
                raise ValidationError(f"Invalid breakdown format: {field} must be a dictionary")
            
            for country, amount in costs.items():
                if not isinstance(country, str):
                    raise ValidationError(f"Invalid breakdown format: {field} keys must be strings")
                try:
                    Decimal(str(amount))
                except (TypeError, ValueError, AttributeError, InvalidOperation):
                    raise ValidationError(f"Invalid breakdown format: value '{amount}' in {field} is not a valid decimal number")
