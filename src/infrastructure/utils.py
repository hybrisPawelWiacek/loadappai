"""Utility functions for infrastructure layer."""
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID


class DecimalUUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal, UUID, and datetime values."""
    def default(self, obj: Any) -> Any:
        """Convert special types for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def decimal_json_dumps(obj: Any) -> str:
    """Dump JSON with Decimal, UUID, and datetime handling."""
    return json.dumps(obj, cls=DecimalUUIDEncoder)


def convert_dict_decimals(data: dict) -> dict:
    """Convert all Decimal values in a dictionary to float."""
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = convert_dict_decimals(value)
        elif isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result
