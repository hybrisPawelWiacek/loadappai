"""Tests for infrastructure utility functions."""
import json
from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import UUID
import pytest

from src.infrastructure.utils import (
    DecimalUUIDEncoder,
    decimal_json_dumps,
    decimal_json_loads,
    convert_dict_decimals,
    safe_decimal,
    utc_now,
    format_currency,
    remove_none_values
)

# Test data
SAMPLE_UUID = UUID('12345678-1234-5678-1234-567812345678')
SAMPLE_DECIMAL = Decimal('123.45')
SAMPLE_DATE = date(2024, 1, 1)
SAMPLE_DATETIME = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

def test_decimal_uuid_encoder():
    """Test custom JSON encoder for special types."""
    encoder = DecimalUUIDEncoder()
    
    assert encoder.default(SAMPLE_DECIMAL) == float(SAMPLE_DECIMAL)
    assert encoder.default(SAMPLE_UUID) == str(SAMPLE_UUID)
    assert encoder.default(SAMPLE_DATE) == SAMPLE_DATE.isoformat()
    assert encoder.default(SAMPLE_DATETIME) == SAMPLE_DATETIME.isoformat()
    
    with pytest.raises(TypeError):
        encoder.default(object())

def test_decimal_json_dumps():
    """Test JSON serialization with special type handling."""
    data = {
        'decimal': SAMPLE_DECIMAL,
        'uuid': SAMPLE_UUID,
        'date': SAMPLE_DATE,
        'datetime': SAMPLE_DATETIME
    }
    
    json_str = decimal_json_dumps(data)
    parsed = json.loads(json_str)
    
    assert parsed['decimal'] == float(SAMPLE_DECIMAL)
    assert parsed['uuid'] == str(SAMPLE_UUID)
    assert parsed['date'] == SAMPLE_DATE.isoformat()
    assert parsed['datetime'] == SAMPLE_DATETIME.isoformat()

def test_decimal_json_loads():
    """Test JSON deserialization with decimal handling."""
    json_str = '{"amount": 123.45, "quantity": 100}'
    data = decimal_json_loads(json_str)
    
    assert isinstance(data['amount'], Decimal)
    assert data['amount'] == Decimal('123.45')
    assert isinstance(data['quantity'], Decimal)
    assert data['quantity'] == Decimal('100')
    
    with pytest.raises(json.JSONDecodeError):
        decimal_json_loads('invalid json')

def test_convert_dict_decimals():
    """Test dictionary conversion for special types."""
    data = {
        'amount': SAMPLE_DECIMAL,
        'id': SAMPLE_UUID,
        'date': SAMPLE_DATE,
        'nested': {'value': SAMPLE_DECIMAL},
        'list': [{'value': SAMPLE_DECIMAL}]
    }
    
    converted = convert_dict_decimals(data)
    
    assert isinstance(converted['amount'], float)
    assert converted['amount'] == float(SAMPLE_DECIMAL)
    assert converted['id'] == str(SAMPLE_UUID)
    assert converted['date'] == SAMPLE_DATE.isoformat()
    assert isinstance(converted['nested']['value'], float)
    assert isinstance(converted['list'][0]['value'], float)
    
    with pytest.raises(ValueError):
        convert_dict_decimals({'value': object()})

def test_safe_decimal():
    """Test safe decimal conversion."""
    assert safe_decimal('123.45') == Decimal('123.45')
    assert safe_decimal(123.45) == Decimal('123.45')
    assert safe_decimal(123) == Decimal('123')
    assert safe_decimal(None) is None
    assert safe_decimal(None, Decimal('0')) == Decimal('0')
    assert safe_decimal('invalid', Decimal('0')) == Decimal('0')

def test_utc_now():
    """Test UTC datetime generation."""
    now = utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc

def test_format_currency():
    """Test currency formatting."""
    assert format_currency(Decimal('123.456'), 'USD', 2) == '123.46 USD'
    assert format_currency(Decimal('123.45'), 'EUR') == '123.45 EUR'
    assert format_currency(Decimal('123.456'), decimals=3) == '123.456 EUR'
    
    with pytest.raises(ValueError):
        format_currency('invalid')

def test_remove_none_values():
    """Test None value removal from dictionaries."""
    data = {
        'a': 1,
        'b': None,
        'c': {
            'd': None,
            'e': 2
        },
        'f': [{'g': None, 'h': 3}]
    }
    
    cleaned = remove_none_values(data)
    
    assert 'b' not in cleaned
    assert 'd' not in cleaned['c']
    assert cleaned == {
        'a': 1,
        'c': {'e': 2},
        'f': [{'g': None, 'h': 3}]  # List items are preserved
    }
