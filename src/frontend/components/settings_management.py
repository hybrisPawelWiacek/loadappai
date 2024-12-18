"""
Settings management component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, Optional
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class CostSettings:
    """Data class for cost calculation settings."""
    base_rate_per_km: Decimal
    fuel_price_per_liter: Decimal
    toll_rate_per_km: Decimal
    empty_driving_factor: float
    margin_percentage: float
    currency: str = "EUR"

def render_settings_management():
    """Render the settings management interface."""
    st.header("Settings Management")
    
    # Create tabs for different settings categories
    cost_tab, transport_tab, system_tab = st.tabs([
        "Cost Settings",
        "Transport Settings",
        "System Settings"
    ])
    
    with cost_tab:
        render_cost_settings()
    
    with transport_tab:
        render_transport_settings()
    
    with system_tab:
        render_system_settings()

def render_cost_settings():
    """Render cost-related settings."""
    st.subheader("Cost Calculation Settings")
    
    with st.form("cost_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            base_rate = st.number_input(
                "Base Rate per km (€)",
                min_value=0.0,
                value=1.5,
                step=0.1,
                format="%.2f",
                help="Base cost per kilometer excluding fuel and tolls"
            )
            
            fuel_price = st.number_input(
                "Fuel Price (€/L)",
                min_value=0.0,
                value=1.8,
                step=0.1,
                format="%.2f",
                help="Current fuel price per liter"
            )
        
        with col2:
            toll_rate = st.number_input(
                "Toll Rate per km (€)",
                min_value=0.0,
                value=0.2,
                step=0.1,
                format="%.2f",
                help="Average toll cost per kilometer"
            )
            
            empty_factor = st.slider(
                "Empty Driving Factor",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="Factor to apply to return journey costs"
            )
        
        margin = st.slider(
            "Default Margin (%)",
            min_value=0,
            max_value=50,
            value=15,
            help="Default profit margin percentage"
        )
        
        currency = st.selectbox(
            "Currency",
            ["EUR", "USD", "GBP"],
            index=0,
            help="Currency for all cost calculations"
        )
        
        if st.form_submit_button("Save Cost Settings"):
            # TODO: Implement settings save functionality
            st.success("Cost settings saved successfully!")

def render_transport_settings():
    """Render transport-related settings."""
    st.subheader("Transport Settings")
    
    with st.form("transport_settings"):
        # Transport types configuration
        st.markdown("#### Transport Types")
        transport_types = st.multiselect(
            "Available Transport Types",
            ["Truck", "Van", "Container", "Refrigerated Truck", "Tanker"],
            default=["Truck", "Van", "Container"],
            help="Select available transport types"
        )
        
        # Cargo types configuration
        st.markdown("#### Cargo Types")
        cargo_types = st.multiselect(
            "Available Cargo Types",
            [
                "General",
                "Temperature Controlled",
                "Hazardous",
                "Bulk",
                "Liquid",
                "Heavy"
            ],
            default=["General", "Temperature Controlled", "Hazardous"],
            help="Select available cargo types"
        )
        
        # Additional services configuration
        st.markdown("#### Additional Services")
        services = st.multiselect(
            "Available Additional Services",
            [
                "Loading assistance",
                "Unloading assistance",
                "Real-time tracking",
                "Insurance",
                "Express delivery",
                "Customs clearance"
            ],
            default=[
                "Loading assistance",
                "Unloading assistance",
                "Real-time tracking"
            ],
            help="Select available additional services"
        )
        
        if st.form_submit_button("Save Transport Settings"):
            # TODO: Implement settings save functionality
            st.success("Transport settings saved successfully!")

def render_system_settings():
    """Render system-related settings."""
    st.subheader("System Settings")
    
    with st.form("system_settings"):
        # API configuration
        st.markdown("#### API Settings")
        api_url = st.text_input(
            "API URL",
            value="http://localhost:8000",
            help="Base URL for the backend API"
        )
        
        # Map settings
        st.markdown("#### Map Settings")
        default_zoom = st.slider(
            "Default Map Zoom Level",
            min_value=1,
            max_value=20,
            value=10,
            help="Default zoom level for map displays"
        )
        
        map_provider = st.selectbox(
            "Map Provider",
            ["Google Maps", "OpenStreetMap"],
            help="Select the map provider for route visualization"
        )
        
        # Cache settings
        st.markdown("#### Cache Settings")
        enable_cache = st.checkbox(
            "Enable Response Caching",
            value=True,
            help="Cache API responses for better performance"
        )
        
        if enable_cache:
            cache_duration = st.number_input(
                "Cache Duration (minutes)",
                min_value=1,
                value=60,
                help="How long to cache API responses"
            )
        
        if st.form_submit_button("Save System Settings"):
            # TODO: Implement settings save functionality
            st.success("System settings saved successfully!")
