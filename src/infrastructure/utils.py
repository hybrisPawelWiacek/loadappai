"""Utility functions for infrastructure layer."""
import json
from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class DecimalUUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal, UUID, datetime, and date values."""
    def default(self, obj: Any) -> Any:
        """Convert special types for JSON serialization.
        
        Args:
            obj: Object to convert.
            
        Returns:
            JSON serializable value.
            
        Raises:
            TypeError: If object cannot be serialized.
        """
        try:
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, UUID):
                return str(obj)
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return super().default(obj)
        except Exception as e:
            logger.error("JSON encoding error", error=str(e), object_type=type(obj))
            raise


def decimal_json_dumps(obj: Any, **kwargs) -> str:
    """Dump JSON with Decimal, UUID, datetime, and date handling.
    
    Args:
        obj: Object to serialize.
        **kwargs: Additional arguments passed to json.dumps.
        
    Returns:
        JSON string.
        
    Raises:
        TypeError: If object cannot be serialized.
    """
    try:
        return json.dumps(obj, cls=DecimalUUIDEncoder, **kwargs)
    except Exception as e:
        logger.error("JSON dumps error", error=str(e), object_type=type(obj))
        raise


def decimal_json_loads(json_str: str) -> Any:
    """Load JSON string with proper decimal handling.
    
    Args:
        json_str: JSON string to parse.
        
    Returns:
        Parsed JSON data.
        
    Raises:
        JSONDecodeError: If JSON string is invalid.
    """
    try:
        return json.loads(json_str, parse_float=Decimal, parse_int=Decimal)
    except json.JSONDecodeError as e:
        logger.error("JSON decode error", error=str(e))
        raise


def convert_dict_decimals(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all Decimal, UUID, datetime, and date values in a dictionary to serializable types.
    
    Args:
        data: Dictionary to convert.
        
    Returns:
        Dictionary with converted values.
        
    Raises:
        ValueError: If conversion fails.
    """
    try:
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = convert_dict_decimals(value)
            elif isinstance(value, list):
                result[key] = [convert_dict_decimals(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif value is not None and not isinstance(value, (str, int, float, bool)):
                raise ValueError(f"Cannot convert value of type {type(value)}")
            else:
                result[key] = value
        return result
    except Exception as e:
        logger.error("Dictionary conversion error", error=str(e))
        raise ValueError(f"Failed to convert dictionary: {str(e)}")


def safe_decimal(value: Union[str, float, int, Decimal, None], default: Optional[Decimal] = None) -> Optional[Decimal]:
    """Safely convert a value to Decimal.
    
    Args:
        value: Value to convert.
        default: Default value if conversion fails.
        
    Returns:
        Decimal value or default if conversion fails.
    """
    if value is None:
        return default
        
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning("Decimal conversion failed", value=value, error=str(e))
        return default


def utc_now() -> datetime:
    """Get current UTC datetime.
    
    Returns:
        Current UTC datetime.
    """
    return datetime.now(timezone.utc)


def format_currency(amount: Decimal, currency: str = "EUR", decimals: int = 2) -> str:
    """Format currency amount.
    
    Args:
        amount: Amount to format.
        currency: Currency code.
        decimals: Number of decimal places.
        
    Returns:
        Formatted currency string.
        
    Raises:
        ValueError: If amount is invalid.
    """
    try:
        return f"{float(amount):.{decimals}f} {currency}"
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.error("Currency formatting error", amount=amount, currency=currency, error=str(e))
        raise ValueError(f"Invalid currency amount: {amount}")


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dictionary recursively.
    
    Args:
        data: Dictionary to clean.
        
    Returns:
        Dictionary without None values.
    """
    return {
        key: remove_none_values(value) if isinstance(value, dict) else value
        for key, value in data.items()
        if value is not None
    }
