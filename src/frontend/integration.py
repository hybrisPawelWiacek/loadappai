"""
Integration module for frontend-backend communication
"""
import os
from datetime import datetime, timezone
from typing import List, Tuple, Optional
import requests
import streamlit as st
from decimal import Decimal

from src.frontend.components.route_form import RouteFormData, Location
from src.frontend.components.map_visualization import RouteSegment, TimelineEventType
from src.frontend.components.cost_calculation import EnhancedCostBreakdown

def submit_route(form_data: RouteFormData) -> Tuple[List[RouteSegment], datetime, str]:
    """Submit route data to backend API and convert response to frontend models."""
    # Prepare request data with default cargo specs
    default_cargo_specs = {
        "weight_kg": 1000,
        "volume_m3": 10,
        "cargo_type": "general",  # Added required field
        "length_m": 2,
        "width_m": 2,
        "height_m": 2,
        "temperature_controlled": False,
        "required_temp_celsius": None,
        "hazmat_class": None
    }
    
    request_data = {
        "origin": {
            "address": form_data.origin.address,
            "latitude": form_data.origin.latitude,
            "longitude": form_data.origin.longitude,
            "country": form_data.origin.country
        },
        "destination": {
            "address": form_data.destination.address,
            "latitude": form_data.destination.latitude,
            "longitude": form_data.destination.longitude,
            "country": form_data.destination.country
        },
        "transport_type": form_data.transport_type,
        "pickup_time": form_data.pickup_time.isoformat(),
        "delivery_time": form_data.delivery_time.isoformat(),
        "cargo_specs": default_cargo_specs
    }

    # Send request to backend
    api_url = "http://localhost:5001/api/v1/routes"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": "development"
    }
    
    print("Sending request to API:", request_data)
    try:
        response = requests.post(api_url, json=request_data, headers=headers)
        print("Received response from API:", response.json())
        
        if response.status_code != 201:
            raise Exception(f"Error from backend: {response.text}")
            
        route_data = response.json()
        segments = []
        route_id = route_data.get("id")  # Get route ID from response
        
        # Use API segments if available
        if route_data.get("segments"):
            for segment in route_data["segments"]:
                segments.append(RouteSegment(
                    start_location=Location(
                        address=segment["start_location"]["address"],
                        latitude=segment["start_location"]["latitude"],
                        longitude=segment["start_location"]["longitude"],
                        country=segment["start_location"]["country"]
                    ),
                    end_location=Location(
                        address=segment["end_location"]["address"],
                        latitude=segment["end_location"]["latitude"],
                        longitude=segment["end_location"]["longitude"],
                        country=segment["end_location"]["country"]
                    ),
                    distance_km=segment["distance_km"],
                    duration_hours=segment["duration_hours"],
                    country=segment["country"],
                    is_empty_driving=segment.get("is_empty_driving", False),
                    timeline_event=TimelineEventType(segment.get("timeline_event", "loaded_driving"))
                ))
        else:
            # Add empty driving segment if present
            if route_data.get("empty_driving"):
                empty = route_data["empty_driving"]
                segments.append(RouteSegment(
                    start_location=Location(
                        address=empty["start_location"]["address"],
                        latitude=empty["start_location"]["latitude"],
                        longitude=empty["start_location"]["longitude"],
                        country=empty["start_location"]["country"]
                    ),
                    end_location=Location(
                        address=empty["end_location"]["address"],
                        latitude=empty["end_location"]["latitude"],
                        longitude=empty["end_location"]["longitude"],
                        country=empty["end_location"]["country"]
                    ),
                    distance_km=empty["distance_km"],
                    duration_hours=empty["duration_hours"],
                    country=empty["start_location"]["country"],
                    is_empty_driving=True,
                    timeline_event=TimelineEventType.EMPTY_DRIVING
                ))
            
            # Add main route segment
            segments.append(RouteSegment(
                start_location=Location(
                    address=route_data["origin"]["address"],
                    latitude=route_data["origin"]["latitude"],
                    longitude=route_data["origin"]["longitude"],
                    country=route_data["origin"]["country"]
                ),
                end_location=Location(
                    address=route_data["destination"]["address"],
                    latitude=route_data["destination"]["latitude"],
                    longitude=route_data["destination"]["longitude"],
                    country=route_data["destination"]["country"]
                ),
                distance_km=route_data["distance_km"],
                duration_hours=route_data["duration_hours"],
                country=route_data["origin"]["country"],
                is_empty_driving=False,
                timeline_event=TimelineEventType.LOADED_DRIVING
            ))
        
        print("Converted to segments:", segments)
        print("Pickup time:", form_data.pickup_time)
        
        # Return segments, pickup time, and route ID
        return segments, form_data.pickup_time, route_id
        
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to backend server. Please make sure it's running on http://localhost:5001")
    except Exception as e:
        raise Exception(f"Error communicating with backend: {str(e)}")

def get_route_cost(route_id: str) -> Optional[EnhancedCostBreakdown]:
    """Get cost calculation for a route from backend API."""
    api_url = f"http://localhost:5001/api/v1/routes/{route_id}/cost"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": "development"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            print(f"Error getting cost calculation: {response.text}")
            return None
            
        cost_data = response.json()
        breakdown = cost_data.get("breakdown", {})
        
        # Convert cost data to EnhancedCostBreakdown
        return EnhancedCostBreakdown(
            fuel_costs={k: Decimal(str(v)) for k, v in breakdown.get("fuel_costs", {}).items()},
            toll_costs={k: Decimal(str(v)) for k, v in breakdown.get("toll_costs", {}).items()},
            driver_costs={k: Decimal(str(v)) for k, v in breakdown.get("driver_costs", {}).items()},
            rest_period_costs=Decimal(str(breakdown.get("rest_period_costs", 0))),
            loading_unloading_costs=Decimal(str(breakdown.get("loading_unloading_costs", 0))),
            empty_driving_costs={
                k: {sk: Decimal(str(sv)) for sk, sv in v.items()}
                for k, v in breakdown.get("empty_driving_costs", {}).items()
            },
            cargo_specific_costs={},  # Initialize empty as it's not in current response
            overheads=breakdown.get("overheads", {
                "distance": Decimal("0"),
                "time": Decimal("0"),
                "fixed": Decimal("0")
            }),
            calculation_method="standard",
            is_final=True,
            version="2.0",
            currency=cost_data.get("currency", "EUR")
        )
    except Exception as e:
        print(f"Error getting cost calculation: {str(e)}")
        return None

def handle_route_submission(form_data: RouteFormData) -> Optional[Tuple[List[RouteSegment], datetime, str]]:
    """Handle route form submission."""
    try:
        # Submit route to API
        segments, pickup_time, route_id = submit_route(form_data)
        return segments, pickup_time, route_id
        
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
