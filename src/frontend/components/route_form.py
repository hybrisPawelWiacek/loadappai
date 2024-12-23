"""
Route input form component for LoadApp.AI
"""
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class TransportType(str, Enum):
    """Valid transport types matching API specification."""
    TRUCK = "truck"
    VAN = "van"
    TRAILER = "trailer"

@dataclass
class Location:
    """Location data matching API specification."""
    address: str
    latitude: float
    longitude: float
    country: str

@dataclass
class CargoSpecification:
    """Cargo specifications matching API specification."""
    weight_kg: float
    volume_m3: float
    cargo_type: str
    hazmat_class: Optional[str] = None
    temperature_controlled: bool = False
    required_temp_celsius: Optional[float] = None

@dataclass
class RouteFormData:
    """Data class for route form inputs matching API specification."""
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    transport_type: TransportType
    cargo_specs: Optional[CargoSpecification] = None

def get_location_details(address: str) -> Optional[Location]:
    """Get location details from address using geocoding service.
    
    Args:
        address: Address string to geocode
        
    Returns:
        Location object if successful, None if geocoding fails
    """
    # For now, return hardcoded coordinates for Warsaw and Berlin
    # TODO: Implement actual geocoding service
    # For now return mock data
    if "Warsaw" in address:
        return Location(
            address="Warsaw, Poland",
            latitude=52.2297,
            longitude=21.0122,
            country="Poland"
        )
    elif "Berlin" in address:
        return Location(
            address="Berlin, Germany",
            latitude=52.5200,
            longitude=13.4050,
            country="Germany"
        )
    return None

def render_route_form() -> Optional[RouteFormData]:
    """Render the route input form with validation and API-compatible data.
    
    Returns:
        RouteFormData if form is submitted successfully, None otherwise
    """
    # Initialize form data in session state
    if "form_origin" not in st.session_state:
        st.session_state.form_origin = "Warsaw, Poland"
    if "form_destination" not in st.session_state:
        st.session_state.form_destination = "Berlin, Germany"
    if "form_transport_type" not in st.session_state:
        st.session_state.form_transport_type = TransportType.TRUCK
    if "form_pickup_time" not in st.session_state:
        st.session_state.form_pickup_time = datetime.now() + timedelta(hours=1)
    if "form_delivery_time" not in st.session_state:
        st.session_state.form_delivery_time = datetime.now() + timedelta(hours=24)
    
    # Cargo specifications
    if "form_cargo_weight" not in st.session_state:
        st.session_state.form_cargo_weight = 1000.0
    if "form_cargo_volume" not in st.session_state:
        st.session_state.form_cargo_volume = 20.0
    if "form_cargo_type" not in st.session_state:
        st.session_state.form_cargo_type = "General"
    if "form_temp_controlled" not in st.session_state:
        st.session_state.form_temp_controlled = False
    if "form_temp_celsius" not in st.session_state:
        st.session_state.form_temp_celsius = 0.0
    if "form_hazmat_class" not in st.session_state:
        st.session_state.form_hazmat_class = ""
    
    with st.form("route_form"):
        st.subheader("Route Details")
        col1, col2 = st.columns(2)
        
        with col1:
            origin = st.text_input(
                "Origin Address",
                value=st.session_state.form_origin,
                placeholder="Enter pickup location",
                key="origin_input"
            )
            
            # Split datetime input into date and time
            pickup_date = st.date_input(
                "Pickup Date",
                value=st.session_state.form_pickup_time.date(),
                min_value=datetime.now().date(),
                key="pickup_date_input"
            )
            pickup_time = st.time_input(
                "Pickup Time",
                value=st.session_state.form_pickup_time.time(),
                key="pickup_time_input"
            )
            # Combine date and time
            pickup_datetime = datetime.combine(pickup_date, pickup_time)
            
            transport_type = st.selectbox(
                "Transport Type",
                [t.value for t in TransportType],
                index=[t.value for t in TransportType].index(st.session_state.form_transport_type.value),
                help="Select the type of transport needed",
                key="transport_type_input"
            )
        
        with col2:
            destination = st.text_input(
                "Destination Address",
                value=st.session_state.form_destination,
                placeholder="Enter delivery location",
                key="destination_input"
            )
            
            # Split datetime input into date and time
            delivery_date = st.date_input(
                "Delivery Date",
                value=st.session_state.form_delivery_time.date(),
                min_value=datetime.now().date(),
                key="delivery_date_input"
            )
            delivery_time = st.time_input(
                "Delivery Time",
                value=st.session_state.form_delivery_time.time(),
                key="delivery_time_input"
            )
            # Combine date and time
            delivery_datetime = datetime.combine(delivery_date, delivery_time)
        
        st.subheader("Cargo Details")
        cargo_col1, cargo_col2 = st.columns(2)
        
        with cargo_col1:
            cargo_weight = st.number_input(
                "Cargo Weight (kg)",
                value=st.session_state.form_cargo_weight,
                min_value=0.1,
                help="Enter the weight of cargo in kilograms",
                key="cargo_weight_input"
            )
            
            cargo_type = st.selectbox(
                "Cargo Type",
                ["General", "Temperature Controlled", "Hazardous", "Bulk"],
                index=["General", "Temperature Controlled", "Hazardous", "Bulk"].index(st.session_state.form_cargo_type),
                help="Select the type of cargo being transported",
                key="cargo_type_input"
            )
            
            temp_controlled = st.checkbox(
                "Temperature Controlled",
                value=st.session_state.form_temp_controlled,
                key="temp_controlled_input"
            )
        
        with cargo_col2:
            cargo_volume = st.number_input(
                "Cargo Volume (m³)",
                value=st.session_state.form_cargo_volume,
                min_value=0.1,
                help="Enter the volume of cargo in cubic meters",
                key="cargo_volume_input"
            )
            
            hazmat_class = st.text_input(
                "Hazmat Class",
                value=st.session_state.form_hazmat_class,
                placeholder="Optional: Enter hazmat class",
                help="Leave empty if not hazardous",
                key="hazmat_class_input"
            ) if cargo_type == "Hazardous" else ""
            
            temp_celsius = st.number_input(
                "Required Temperature (°C)",
                value=st.session_state.form_temp_celsius,
                help="Required temperature for temperature-controlled cargo",
                key="temp_celsius_input"
            ) if temp_controlled else None
        
        submitted = st.form_submit_button("Calculate Route", type="primary")
        
        if submitted:
            # Validate inputs
            if not origin or not destination:
                st.error("Please enter both origin and destination addresses.")
                return None
            
            if pickup_datetime >= delivery_datetime:
                st.error("Delivery time must be after pickup time.")
                return None
            
            # Get location details
            origin_location = get_location_details(origin)
            destination_location = get_location_details(destination)
            
            if not origin_location or not destination_location:
                return None
            
            # Create cargo specifications if needed
            cargo_specs = CargoSpecification(
                weight_kg=cargo_weight,
                volume_m3=cargo_volume,
                cargo_type=cargo_type,
                hazmat_class=hazmat_class if cargo_type == "Hazardous" else None,
                temperature_controlled=temp_controlled,
                required_temp_celsius=temp_celsius if temp_controlled else None
            )
            
            # Update session state
            st.session_state.form_origin = origin
            st.session_state.form_destination = destination
            st.session_state.form_transport_type = TransportType(transport_type)
            st.session_state.form_pickup_time = pickup_datetime
            st.session_state.form_delivery_time = delivery_datetime
            st.session_state.form_cargo_weight = cargo_weight
            st.session_state.form_cargo_volume = cargo_volume
            st.session_state.form_cargo_type = cargo_type
            st.session_state.form_temp_controlled = temp_controlled
            st.session_state.form_temp_celsius = temp_celsius
            st.session_state.form_hazmat_class = hazmat_class
            
            return RouteFormData(
                origin=origin_location,
                destination=destination_location,
                pickup_time=pickup_datetime,
                delivery_time=delivery_datetime,
                transport_type=TransportType(transport_type),
                cargo_specs=cargo_specs
            )
        
        return None

def display_route_summary(route_data: RouteFormData):
    """Display a summary of the route information.
    
    Args:
        route_data: The submitted route form data
    """
    st.subheader("Route Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Origin**")
        st.write(route_data.origin.address)
        st.markdown("**Transport Type**")
        st.write(route_data.transport_type.value)
    
    with col2:
        st.markdown("**Destination**")
        st.write(route_data.destination.address)
        st.markdown("**Cargo Type**")
        st.write(route_data.cargo_specs.cargo_type if route_data.cargo_specs else "None")
    
    if route_data.cargo_specs:
        st.markdown("**Cargo Specifications**")
        st.write(f"Weight: {route_data.cargo_specs.weight_kg} kg")
        st.write(f"Volume: {route_data.cargo_specs.volume_m3} m³")
        if route_data.cargo_specs.temperature_controlled:
            st.write(f"Temperature: {route_data.cargo_specs.required_temp_celsius} °C")
        if route_data.cargo_specs.hazmat_class:
            st.write(f"Hazmat Class: {route_data.cargo_specs.hazmat_class}")
