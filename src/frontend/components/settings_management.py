"""
Settings management component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, Optional, List
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class EnhancedCostSettings:
    """Data class for enhanced cost calculation settings."""
    # Base rates per country
    base_rates: Dict[str, Dict[str, Decimal]]  # country -> rate_type -> value
    # Time-based costs
    time_based_rates: Dict[str, Decimal]  # rate_type -> value
    # Empty driving factors
    empty_driving_factors: Dict[str, float]  # country -> factor
    # Cargo-specific factors
    cargo_factors: Dict[str, float]  # cargo_type -> factor
    # Equipment costs
    equipment_costs: Dict[str, Decimal]  # equipment_type -> cost
    # Business settings
    margin_percentage: float
    currency: str = "EUR"
    version: str = "2.0"

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
        render_enhanced_cost_settings()
    
    with transport_tab:
        render_transport_settings()
    
    with system_tab:
        render_system_settings()

def render_enhanced_cost_settings():
    """Render enhanced cost-related settings."""
    st.subheader("Cost Calculation Settings")
    
    with st.form("enhanced_cost_settings"):
        # Country-specific base rates
        st.markdown("### Base Rates by Country")
        countries = ["Germany", "France", "Netherlands", "Belgium", "Poland"]
        selected_countries = st.multiselect(
            "Select Countries",
            countries,
            default=countries[:3]
        )
        
        for country in selected_countries:
            st.markdown(f"#### {country}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input(
                    f"Fuel Rate (€/L) - {country}",
                    min_value=0.0,
                    value=1.8,
                    step=0.1,
                    format="%.2f",
                    key=f"fuel_rate_{country}"
                )
            
            with col2:
                st.number_input(
                    f"Driver Rate (€/h) - {country}",
                    min_value=0.0,
                    value=25.0,
                    step=1.0,
                    format="%.2f",
                    key=f"driver_rate_{country}"
                )
            
            with col3:
                st.number_input(
                    f"Toll Rate (€/km) - {country}",
                    min_value=0.0,
                    value=0.2,
                    step=0.1,
                    format="%.2f",
                    key=f"toll_rate_{country}"
                )
        
        # Time-based costs
        st.markdown("### Time-Based Costs")
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input(
                "Rest Period Cost (€/h)",
                min_value=0.0,
                value=20.0,
                step=1.0,
                format="%.2f",
                key="rest_period_rate"
            )
        
        with col2:
            st.number_input(
                "Loading/Unloading Cost (€/h)",
                min_value=0.0,
                value=30.0,
                step=1.0,
                format="%.2f",
                key="loading_unloading_rate"
            )
        
        # Empty driving factors
        st.markdown("### Empty Driving Factors")
        for country in selected_countries:
            st.slider(
                f"Empty Driving Factor - {country}",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                key=f"empty_factor_{country}",
                help=f"Factor to apply to return journey costs in {country}"
            )
        
        # Cargo-specific factors
        st.markdown("### Cargo-Specific Factors")
        cargo_types = [
            "General",
            "Temperature Controlled",
            "Hazardous",
            "Heavy",
            "Fragile"
        ]
        
        col1, col2 = st.columns(2)
        for i, cargo_type in enumerate(cargo_types):
            with col1 if i % 2 == 0 else col2:
                st.number_input(
                    f"{cargo_type} Factor",
                    min_value=1.0,
                    value=1.0 + (0.2 * (i + 1)),
                    step=0.1,
                    format="%.2f",
                    key=f"cargo_factor_{cargo_type}",
                    help=f"Cost multiplier for {cargo_type} cargo"
                )
        
        # Equipment costs
        st.markdown("### Equipment Costs")
        equipment_types = [
            "Refrigeration",
            "Tail Lift",
            "GPS Tracking",
            "Security Seals",
            "Load Bars"
        ]
        
        col1, col2 = st.columns(2)
        for i, equipment in enumerate(equipment_types):
            with col1 if i % 2 == 0 else col2:
                st.number_input(
                    f"{equipment} Cost (€/day)",
                    min_value=0.0,
                    value=50.0 * (i + 1),
                    step=10.0,
                    format="%.2f",
                    key=f"equipment_cost_{equipment}"
                )
        
        # Business settings
        st.markdown("### Business Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            margin = st.slider(
                "Default Margin (%)",
                min_value=0,
                max_value=50,
                value=15,
                help="Default profit margin percentage"
            )
        
        with col2:
            currency = st.selectbox(
                "Currency",
                ["EUR", "USD", "GBP"],
                index=0,
                help="Currency for all cost calculations"
            )
        
        if st.form_submit_button("Save Cost Settings"):
            # TODO: Implement settings save functionality
            st.success("Enhanced cost settings saved successfully!")

def render_transport_settings():
    """Render transport-related settings."""
    st.subheader("Transport Settings")
    
    with st.form("transport_settings"):
        # Vehicle types configuration
        st.markdown("#### Vehicle Types")
        vehicle_types = st.multiselect(
            "Available Vehicle Types",
            [
                "Standard Truck",
                "Refrigerated Truck",
                "Box Truck",
                "Flatbed",
                "Tanker",
                "Container Carrier"
            ],
            default=[
                "Standard Truck",
                "Refrigerated Truck",
                "Box Truck"
            ],
            help="Select available vehicle types"
        )
        
        # Vehicle specifications
        st.markdown("#### Vehicle Specifications")
        for vehicle_type in vehicle_types:
            st.markdown(f"##### {vehicle_type}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input(
                    "Max Weight (tons)",
                    min_value=0.0,
                    value=24.0,
                    step=0.5,
                    format="%.1f",
                    key=f"weight_{vehicle_type}"
                )
            
            with col2:
                st.number_input(
                    "Volume (m³)",
                    min_value=0.0,
                    value=80.0,
                    step=1.0,
                    format="%.1f",
                    key=f"volume_{vehicle_type}"
                )
            
            with col3:
                st.number_input(
                    "Length (m)",
                    min_value=0.0,
                    value=13.6,
                    step=0.1,
                    format="%.1f",
                    key=f"length_{vehicle_type}"
                )
        
        # Cargo types configuration
        st.markdown("#### Cargo Types")
        cargo_types = st.multiselect(
            "Available Cargo Types",
            [
                "General",
                "Temperature Controlled",
                "Hazardous",
                "Heavy",
                "Fragile",
                "Liquid",
                "Bulk"
            ],
            default=[
                "General",
                "Temperature Controlled",
                "Hazardous"
            ],
            help="Select available cargo types"
        )
        
        if st.form_submit_button("Save Transport Settings"):
            st.success("Transport settings saved successfully!")

def render_system_settings():
    """Render system-related settings."""
    st.subheader("System Settings")
    
    with st.form("system_settings"):
        # Cost calculation settings
        st.markdown("#### Cost Calculation Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            calculation_method = st.selectbox(
                "Default Calculation Method",
                ["standard", "detailed", "estimated"],
                index=0,
                help="Choose the default cost calculation method"
            )
            
            show_preliminary = st.checkbox(
                "Show Preliminary Costs",
                value=True,
                help="Display non-final cost calculations"
            )
        
        with col2:
            cache_duration = st.number_input(
                "Cost Cache Duration (minutes)",
                min_value=1,
                value=60,
                help="How long to cache cost calculations"
            )
            
            enable_auto_refresh = st.checkbox(
                "Auto-refresh Costs",
                value=True,
                help="Automatically refresh costs when inputs change"
            )
        
        # API settings
        st.markdown("#### API Settings")
        api_url = st.text_input(
            "API URL",
            value="http://localhost:8000",
            help="Base URL for the backend API"
        )
        
        # Cache settings
        st.markdown("#### Cache Settings")
        enable_cache = st.checkbox(
            "Enable Response Caching",
            value=True,
            help="Cache API responses for better performance"
        )
        
        if st.form_submit_button("Save System Settings"):
            st.success("System settings saved successfully!")
