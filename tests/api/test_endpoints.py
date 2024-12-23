"""Test API endpoints."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

@pytest.fixture(scope="function")
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

@pytest.fixture(scope="function")
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

def test_get_offer_history(client, offer_id):
    """Test get offer history endpoint."""
    response = client.get(f"/api/v1/offers/{offer_id}/history")
    assert response.status_code == 200
    
    data = response.get_json()
    assert isinstance(data, dict)
    assert "history" in data
    assert "total" in data
    assert isinstance(data["history"], list)
    
    if len(data["history"]) > 0:
        entry = data["history"][0]
        assert "version" in entry
        assert "change_reason" in entry
        assert "changed_by" in entry
        assert "changed_at" in entry
        assert "offer_data" in entry


def test_get_offer_version(client, offer_id):
    """Test get specific offer version endpoint."""
    # First, get history to find a version
    response = client.get(f"/api/v1/offers/{offer_id}/history")
    assert response.status_code == 200
    
    history = response.get_json()["history"]
    if len(history) > 0:
        version = history[0]["version"]
        
        # Get specific version
        response = client.get(f"/api/v1/offers/{offer_id}/versions/{version}")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["version"] == version
        assert "offer_data" in data


def test_create_offer_with_status(client, route_id):
    """Test creating offer with specific status."""
    offer_data = {
        "route_id": route_id,
        "margin": 0.1,
        "status": "DRAFT",
        "additional_services": ["service1", "service2"],
        "notes": "Test notes",
        "metadata": {"key": "value"}
    }
    
    response = client.post("/api/v1/offers", json=offer_data)
    assert response.status_code == 201
    
    data = response.get_json()
    assert data["status"] == "DRAFT"
    assert data["version"] == "1.0"
    assert data["additional_services"] == ["service1", "service2"]
    assert data["notes"] == "Test notes"
    assert data["metadata"] == {"key": "value"}


def test_update_offer_status(client, offer_id):
    """Test updating offer status."""
    update_data = {
        "status": "ACTIVE",
        "change_reason": "Activating offer"
    }
    
    response = client.put(f"/api/v1/offers/{offer_id}/status", json=update_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "ACTIVE"
    assert data["version"] > "1.0"  # Version should be incremented
    
    # Check history was updated
    history_response = client.get(f"/api/v1/offers/{offer_id}/history")
    assert history_response.status_code == 200
    
    history = history_response.get_json()["history"]
    latest_entry = history[0]
    assert latest_entry["change_reason"] == "Activating offer"


def test_archive_offer(client, offer_id):
    """Test archiving an offer."""
    response = client.post(f"/api/v1/offers/{offer_id}/archive")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "ARCHIVED"
    assert data["version"] > "1.0"  # Version should be incremented


def test_list_offers_with_filters(client):
    """Test listing offers with filters."""
    # Create test offers with different statuses
    route_ids = []
    for _ in range(3):
        response = client.post("/api/v1/routes", json={
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
            "cargo_id": f"cargo_{_}"
        })
        assert response.status_code == 201
        route_ids.append(response.get_json()["id"])
    
    # Create offers with different statuses
    statuses = ["DRAFT", "ACTIVE", "ARCHIVED"]
    for route_id, status in zip(route_ids, statuses):
        offer_data = {
            "route_id": route_id,
            "margin": 0.1,
            "status": status
        }
        response = client.post("/api/v1/offers", json=offer_data)
        assert response.status_code == 201
    
    # Test filtering by status
    response = client.get("/api/v1/offers?status=DRAFT,ACTIVE")
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data["offers"]) == 2
    statuses = [offer["status"] for offer in data["offers"]]
    assert "DRAFT" in statuses
    assert "ACTIVE" in statuses
    assert "ARCHIVED" not in statuses
    
    # Test filtering by date range
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
    response = client.get(f"/api/v1/offers?created_after={yesterday}&created_before={tomorrow}")
    assert response.status_code == 200
    
    # Test filtering by price range
    response = client.get("/api/v1/offers?min_price=100&max_price=1000")
    assert response.status_code == 200
    
    # Test pagination
    response = client.get("/api/v1/offers?page=1&per_page=2")
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data["offers"]) <= 2
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_invalid_status_transition(client, offer_id):
    """Test invalid status transition handling."""
    # Try to archive a draft offer (should fail)
    response = client.post(f"/api/v1/offers/{offer_id}/archive")
    assert response.status_code == 400
    
    data = response.get_json()
    assert "error" in data
    assert "status" in data["error"]


def test_version_conflict(client, offer_id):
    """Test version conflict handling."""
    # Try to update with old version
    update_data = {
        "version": "1.0",
        "status": "ACTIVE",
        "change_reason": "Activating offer"
    }
    
    # First update
    response = client.put(f"/api/v1/offers/{offer_id}", json=update_data)
    assert response.status_code == 200
    
    # Try same update again (should fail)
    response = client.put(f"/api/v1/offers/{offer_id}", json=update_data)
    assert response.status_code == 409  # Conflict
    
    data = response.get_json()
    assert "error" in data
    assert "version" in data["error"]
