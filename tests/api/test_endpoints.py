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

def test_get_route_settings(client, route_id):
    """Test get route settings endpoint."""
    # First request should return default settings
    response = client.get(f"/api/v1/routes/{route_id}/settings")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["route_id"] == route_id
    assert "settings" in data
    assert "metadata" in data
    assert data["metadata"]["version"] == 1
    
    # Verify default settings structure
    settings = data["settings"]
    assert "enabled_components" in settings
    assert "fuel_rates" in settings
    assert "toll_rates" in settings
    assert "driver_rates" in settings
    assert "maintenance_rates" in settings
    assert "overhead_rates" in settings

def test_create_route_settings(client, route_id):
    """Test create route settings endpoint."""
    settings_data = {
        "enabled_components": ["fuel", "toll", "driver"],
        "fuel_rates": {
            "DE": {"rate": 1.8, "currency": "EUR"},
            "FR": {"rate": 1.9, "currency": "EUR"}
        },
        "toll_rates": {
            "DE": {"rate": 0.2, "currency": "EUR"},
            "FR": {"rate": 0.25, "currency": "EUR"}
        },
        "driver_rates": {
            "DE": {"rate": 250.0, "currency": "EUR"},
            "FR": {"rate": 280.0, "currency": "EUR"}
        },
        "maintenance_rates": {
            "rate": 0.1,
            "currency": "EUR"
        },
        "overhead_rates": {
            "rate": 50.0,
            "currency": "EUR"
        }
    }
    
    # Create new settings
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json=settings_data
    )
    assert response.status_code == 201
    
    data = response.get_json()
    assert data["route_id"] == route_id
    assert data["settings"]["enabled_components"] == settings_data["enabled_components"]
    assert data["metadata"]["version"] == 1
    assert data["metadata"]["created_by"] is None
    
    # Try to create settings again (should fail)
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json=settings_data
    )
    assert response.status_code == 409  # Conflict

def test_update_route_settings(client, route_id):
    """Test update route settings endpoint."""
    # First create settings
    initial_settings = {
        "enabled_components": ["fuel", "toll"],
        "fuel_rates": {
            "DE": {"rate": 1.8, "currency": "EUR"}
        },
        "toll_rates": {
            "DE": {"rate": 0.2, "currency": "EUR"}
        }
    }
    
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json=initial_settings
    )
    assert response.status_code == 201
    
    # Update settings
    updated_settings = {
        "enabled_components": ["fuel", "toll", "driver"],
        "fuel_rates": {
            "DE": {"rate": 2.0, "currency": "EUR"}
        },
        "toll_rates": {
            "DE": {"rate": 0.25, "currency": "EUR"}
        },
        "driver_rates": {
            "DE": {"rate": 250.0, "currency": "EUR"}
        }
    }
    
    response = client.put(
        f"/api/v1/routes/{route_id}/settings",
        json=updated_settings
    )
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["route_id"] == route_id
    assert len(data["settings"]["enabled_components"]) == 3
    assert data["metadata"]["version"] == 2
    
    # Verify the changes
    response = client.get(f"/api/v1/routes/{route_id}/settings")
    assert response.status_code == 200
    data = response.get_json()
    assert data["settings"]["fuel_rates"]["DE"]["rate"] == 2.0

def test_route_settings_validation(client, route_id):
    """Test validation for route settings endpoints."""
    # Test missing required fields
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json={"enabled_components": ["fuel"]}  # Missing rates
    )
    assert response.status_code == 400
    
    # Test invalid component name
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json={
            "enabled_components": ["invalid_component"],
            "fuel_rates": {
                "DE": {"rate": 1.8, "currency": "EUR"}
            }
        }
    )
    assert response.status_code == 400
    
    # Test invalid rate value
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json={
            "enabled_components": ["fuel"],
            "fuel_rates": {
                "DE": {"rate": -1.0, "currency": "EUR"}  # Negative rate
            }
        }
    )
    assert response.status_code == 400
    
    # Test invalid currency
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json={
            "enabled_components": ["fuel"],
            "fuel_rates": {
                "DE": {"rate": 1.8, "currency": "INVALID"}
            }
        }
    )
    assert response.status_code == 400

def test_route_settings_not_found(client):
    """Test route settings endpoints with non-existent route."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    
    # Test GET
    response = client.get(f"/api/v1/routes/{non_existent_id}/settings")
    assert response.status_code == 404
    
    # Test POST
    response = client.post(
        f"/api/v1/routes/{non_existent_id}/settings",
        json={
            "enabled_components": ["fuel"],
            "fuel_rates": {
                "DE": {"rate": 1.8, "currency": "EUR"}
            }
        }
    )
    assert response.status_code == 404
    
    # Test PUT
    response = client.put(
        f"/api/v1/routes/{non_existent_id}/settings",
        json={
            "enabled_components": ["fuel"],
            "fuel_rates": {
                "DE": {"rate": 1.8, "currency": "EUR"}
            }
        }
    )
    assert response.status_code == 404

def test_calculate_route_costs(client, route_id):
    """Test calculate route costs endpoint."""
    # Test successful calculation
    response = client.post(f"/api/v1/routes/{route_id}/calculate")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "route_id" in data
    assert data["route_id"] == str(route_id)
    assert "breakdown" in data
    assert "components" in data["breakdown"]
    assert "total" in data["breakdown"]
    assert "amount" in data["breakdown"]["total"]
    assert "currency" in data["breakdown"]["total"]
    assert "metadata" in data
    assert "version" in data["metadata"]
    assert "created_at" in data["metadata"]

    # Test non-existent route
    response = client.post("/api/v1/routes/00000000-0000-0000-0000-000000000000/calculate")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "NOT_FOUND"

def test_get_route_costs(client, route_id):
    """Test get route costs endpoint."""
    # First calculate costs
    response = client.post(f"/api/v1/routes/{route_id}/calculate")
    assert response.status_code == 200

    # Then get the costs
    response = client.get(f"/api/v1/routes/{route_id}/costs")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "route_id" in data
    assert data["route_id"] == str(route_id)
    assert "breakdown" in data
    assert "components" in data["breakdown"]
    assert "total" in data["breakdown"]
    assert "amount" in data["breakdown"]["total"]
    assert "currency" in data["breakdown"]["total"]
    assert "metadata" in data
    assert "version" in data["metadata"]
    assert "created_at" in data["metadata"]

    # Test non-existent route
    response = client.get("/api/v1/routes/00000000-0000-0000-0000-000000000000/costs")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "NOT_FOUND"

    # Test route with no costs calculated
    # First create a new route
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
    new_route_id = response.get_json()["id"]

    # Then try to get costs without calculating first
    response = client.get(f"/api/v1/routes/{new_route_id}/costs")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "NOT_FOUND"

def test_route_settings_endpoints(client, route_id):
    """Test route settings endpoints."""
    # Test GET without settings
    response = client.get(f"/api/v1/routes/{route_id}/settings")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"

    # Test POST to create settings
    settings_data = {
        "fuel_rates": {
            "DE": "1.50",
            "FR": "1.60"
        },
        "toll_rates": {
            "DE": {
                "flatbed_truck": "0.20"
            },
            "FR": {
                "flatbed_truck": "0.25"
            }
        },
        "driver_rates": {
            "DE": "30.00",
            "FR": "35.00"
        },
        "overhead_rates": {
            "DE": "100.00",
            "FR": "120.00"
        },
        "maintenance_rates": {
            "flatbed_truck": "0.15"
        },
        "enabled_components": ["fuel", "toll", "driver"]
    }
    
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json=settings_data
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["route_id"] == str(route_id)
    assert "settings" in data
    assert "metadata" in data
    assert data["settings"]["fuel_rates"] == settings_data["fuel_rates"]
    assert data["settings"]["toll_rates"] == settings_data["toll_rates"]
    assert set(data["settings"]["enabled_components"]) == set(settings_data["enabled_components"])

    # Test GET with settings
    response = client.get(f"/api/v1/routes/{route_id}/settings")
    assert response.status_code == 200
    data = response.get_json()
    assert data["route_id"] == str(route_id)
    assert data["settings"]["fuel_rates"] == settings_data["fuel_rates"]
    assert data["settings"]["toll_rates"] == settings_data["toll_rates"]
    assert set(data["settings"]["enabled_components"]) == set(settings_data["enabled_components"])

    # Test PUT to update settings
    updated_settings = settings_data.copy()
    updated_settings["fuel_rates"]["DE"] = "1.55"
    updated_settings["enabled_components"].append("maintenance")
    
    response = client.put(
        f"/api/v1/routes/{route_id}/settings",
        json=updated_settings
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["settings"]["fuel_rates"]["DE"] == "1.55"
    assert "maintenance" in data["settings"]["enabled_components"]

    # Test non-existent route
    response = client.get("/api/v1/routes/00000000-0000-0000-0000-000000000000/settings")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"

    # Test invalid data
    invalid_settings = {
        "fuel_rates": "invalid",  # Should be a dict
        "enabled_components": "invalid"  # Should be a list
    }
    response = client.post(
        f"/api/v1/routes/{route_id}/settings",
        json=invalid_settings
    )
    assert response.status_code == 400
    assert response.get_json()["code"] == "BAD_REQUEST"
