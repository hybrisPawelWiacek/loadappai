"""Test API endpoints."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

@pytest.fixture(scope="module")
def route_id(client):
    """Create a test route and return its ID."""
    route_data = {
        "origin": {
            "address": "Paris, France",
            "latitude": 48.8566,
            "longitude": 2.3522
        },
        "destination": {
            "address": "Frankfurt, Germany",
            "latitude": 50.1109,
            "longitude": 8.6821
        },
        "pickup_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
        "delivery_time": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z",
        "transport_type": "flatbed_truck",
        "cargo_id": "cargo_001"
    }

    response = client.post("/api/v1/routes", json=route_data)
    assert response.status_code == 201
    return response.get_json()["id"]

@pytest.fixture(scope="module")
def offer_id(client, route_id):
    """Create a test offer and return its ID."""
    offer_data = {
        "route_id": route_id,
        "margin": 0.1
    }

    response = client.post("/api/v1/offers", json=offer_data)
    assert response.status_code == 201
    return response.get_json()["id"]

def test_get_route(client, route_id):
    """Test get route endpoint."""
    response = client.get(f"/api/v1/routes/{route_id}")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["id"] == route_id
    assert "origin" in data
    assert "destination" in data
    assert "distance_km" in data

def test_get_route_cost(client, route_id):
    """Test get route cost endpoint."""
    response = client.get(f"/api/v1/routes/{route_id}/cost")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "fuel_cost" in data
    assert "toll_cost" in data
    assert "driver_cost" in data
    assert "total_cost" in data
    assert data["currency"] == "EUR"

def test_get_offer(client, offer_id):
    """Test get offer endpoint."""
    response = client.get(f"/api/v1/offers/{offer_id}")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["id"] == offer_id
    assert "total_cost" in data
    assert "final_price" in data
    assert "fun_fact" in data

def test_list_offers(client):
    """Test list offers endpoint."""
    response = client.get("/api/v1/offers")
    assert response.status_code == 200
    
    data = response.get_json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "final_price" in data[0]

def test_get_cost_settings(client):
    """Test get cost settings endpoint."""
    response = client.get("/api/v1/cost-settings")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "fuel_price_per_liter" in data
    assert "driver_daily_salary" in data
    assert "toll_rates" in data
    assert "overheads" in data
    assert "cargo_factors" in data

def test_update_cost_settings(client):
    """Test update cost settings endpoint."""
    settings_data = {
        "fuel_price_per_liter": 1.60,
        "driver_daily_salary": 140.0,
        "toll_rates": {
            "DE": 0.11,
            "FR": 0.13
        },
        "overheads": {
            "leasing": 22.0,
            "depreciation": 11.0,
            "insurance": 15.0
        },
        "cargo_factors": {
            "cleaning": 12.0,
            "insurance_rate": 0.0012
        }
    }

    response = client.post("/api/v1/cost-settings", json=settings_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "message" in data
    assert "updated_at" in data

def test_validation_errors(client):
    """Test validation error handling."""
    # Test invalid route creation (missing required fields)
    invalid_route = {
        "origin": {
            "address": "Paris, France"
            # Missing latitude and longitude
        }
    }
    response = client.post("/api/v1/routes", json=invalid_route)
    assert response.status_code == 400
    assert "error" in response.get_json()
    
    # Test invalid offer creation (margin out of range)
    invalid_offer = {
        "route_id": "some_id",
        "margin": 2.0  # Invalid margin > 1
    }
    response = client.post("/api/v1/offers", json=invalid_offer)
    assert response.status_code == 400
    assert "error" in response.get_json()
    
    # Test invalid cost settings (negative values)
    invalid_settings = {
        "fuel_price_per_liter": -1.0,  # Invalid negative price
        "driver_daily_salary": 140.0,
        "toll_rates": {"DE": 0.11},
        "overheads": {},
        "cargo_factors": {}
    }
    response = client.post("/api/v1/cost-settings", json=invalid_settings)
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_not_found_errors(client):
    """Test not found error handling."""
    # Test non-existent route
    response = client.get("/api/v1/routes/nonexistent_id")
    assert response.status_code == 404
    assert "error" in response.get_json()
    
    # Test non-existent offer
    response = client.get("/api/v1/offers/nonexistent_id")
    assert response.status_code == 404
    assert "error" in response.get_json()
