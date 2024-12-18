"""
Cost calculation component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, Optional
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class CostBreakdown:
    """Data class for cost breakdown details."""
    # Base costs
    base_cost: Decimal
    # Driver and vehicle costs
    driver_wages: Decimal
    vehicle_costs: Decimal
    # Fuel costs (separated for loaded and empty)
    fuel_cost_loaded: Decimal
    fuel_cost_empty: Optional[Decimal] = None
    # Route-specific costs
    toll_cost: Optional[Decimal] = None
    parking_cost: Optional[Decimal] = None
    # Cargo-specific costs
    cargo_insurance: Optional[Decimal] = None
    cleaning_cost: Optional[Decimal] = None
    temperature_control: Optional[Decimal] = None
    # Business overheads
    leasing_cost: Optional[Decimal] = None
    depreciation: Optional[Decimal] = None
    insurance_cost: Optional[Decimal] = None
    overhead_cost: Optional[Decimal] = None
    
    @property
    def total_fuel_cost(self) -> Decimal:
        """Calculate total fuel cost."""
        return self.fuel_cost_loaded + (self.fuel_cost_empty or Decimal("0"))
    
    @property
    def total_route_costs(self) -> Decimal:
        """Calculate total route-specific costs."""
        total = Decimal("0")
        if self.toll_cost:
            total += self.toll_cost
        if self.parking_cost:
            total += self.parking_cost
        return total
    
    @property
    def total_cargo_costs(self) -> Decimal:
        """Calculate total cargo-specific costs."""
        total = Decimal("0")
        if self.cargo_insurance:
            total += self.cargo_insurance
        if self.cleaning_cost:
            total += self.cleaning_cost
        if self.temperature_control:
            total += self.temperature_control
        return total
    
    @property
    def total_overhead_costs(self) -> Decimal:
        """Calculate total overhead costs."""
        total = Decimal("0")
        if self.leasing_cost:
            total += self.leasing_cost
        if self.depreciation:
            total += self.depreciation
        if self.insurance_cost:
            total += self.insurance_cost
        if self.overhead_cost:
            total += self.overhead_cost
        return total
    
    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost including all components."""
        return (
            self.base_cost +
            self.total_fuel_cost +
            self.driver_wages +
            self.vehicle_costs +
            self.total_route_costs +
            self.total_cargo_costs +
            self.total_overhead_costs
        )

def display_cost_breakdown(cost_data: CostBreakdown):
    """Display a detailed breakdown of transportation costs.
    
    Args:
        cost_data: The cost breakdown data to display
    """
    st.subheader("Cost Breakdown")
    
    # Base costs
    with st.expander("Base Costs", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Base Cost", f"€{cost_data.base_cost:,.2f}")
        with col2:
            st.metric("Vehicle Costs", f"€{cost_data.vehicle_costs:,.2f}")
    
    # Fuel costs
    with st.expander("Fuel Costs", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Loaded Fuel Cost", f"€{cost_data.fuel_cost_loaded:,.2f}")
        with col2:
            if cost_data.fuel_cost_empty:
                st.metric("Empty Driving Fuel Cost", f"€{cost_data.fuel_cost_empty:,.2f}")
        st.metric("Total Fuel Cost", f"€{cost_data.total_fuel_cost:,.2f}")
    
    # Route costs
    if cost_data.total_route_costs > 0:
        with st.expander("Route Costs"):
            col1, col2 = st.columns(2)
            with col1:
                if cost_data.toll_cost:
                    st.metric("Toll Cost", f"€{cost_data.toll_cost:,.2f}")
            with col2:
                if cost_data.parking_cost:
                    st.metric("Parking Cost", f"€{cost_data.parking_cost:,.2f}")
            st.metric("Total Route Costs", f"€{cost_data.total_route_costs:,.2f}")
    
    # Cargo costs
    if cost_data.total_cargo_costs > 0:
        with st.expander("Cargo-Specific Costs"):
            col1, col2 = st.columns(2)
            with col1:
                if cost_data.cargo_insurance:
                    st.metric("Cargo Insurance", f"€{cost_data.cargo_insurance:,.2f}")
                if cost_data.cleaning_cost:
                    st.metric("Cleaning Cost", f"€{cost_data.cleaning_cost:,.2f}")
            with col2:
                if cost_data.temperature_control:
                    st.metric("Temperature Control", f"€{cost_data.temperature_control:,.2f}")
            st.metric("Total Cargo Costs", f"€{cost_data.total_cargo_costs:,.2f}")
    
    # Overhead costs
    if cost_data.total_overhead_costs > 0:
        with st.expander("Business Overheads"):
            col1, col2 = st.columns(2)
            with col1:
                if cost_data.leasing_cost:
                    st.metric("Leasing Cost", f"€{cost_data.leasing_cost:,.2f}")
                if cost_data.depreciation:
                    st.metric("Depreciation", f"€{cost_data.depreciation:,.2f}")
            with col2:
                if cost_data.insurance_cost:
                    st.metric("Insurance Cost", f"€{cost_data.insurance_cost:,.2f}")
                if cost_data.overhead_cost:
                    st.metric("Other Overheads", f"€{cost_data.overhead_cost:,.2f}")
            st.metric("Total Overhead Costs", f"€{cost_data.total_overhead_costs:,.2f}")
    
    # Total cost
    st.markdown("---")
    st.metric(
        "Total Cost",
        f"€{cost_data.total_cost:,.2f}",
        help="Total including all cost components"
    )

def render_cost_settings():
    """Render cost calculation settings and controls."""
    st.subheader("Cost Settings")
    
    with st.expander("Cost Components", expanded=True):
        st.markdown("#### Enable/Disable Cost Components")
        col1, col2 = st.columns(2)
        
        with col1:
            include_empty_driving = st.checkbox(
                "Include Empty Driving",
                value=True,
                help="Calculate costs for return journey without cargo"
            )
            include_tolls = st.checkbox(
                "Include Toll Costs",
                value=True,
                help="Calculate and include toll costs in the total"
            )
            include_parking = st.checkbox(
                "Include Parking Costs",
                value=True,
                help="Include estimated parking costs"
            )
        
        with col2:
            include_cargo_insurance = st.checkbox(
                "Include Cargo Insurance",
                value=True,
                help="Add cargo insurance costs"
            )
            include_cleaning = st.checkbox(
                "Include Cleaning Costs",
                value=True,
                help="Add vehicle cleaning costs"
            )
            include_overheads = st.checkbox(
                "Include Business Overheads",
                value=True,
                help="Include business overhead costs"
            )
    
    with st.expander("Base Rates"):
        col1, col2 = st.columns(2)
        
        with col1:
            fuel_price = st.number_input(
                "Fuel Price (€/L)",
                min_value=0.0,
                value=1.8,
                step=0.1,
                format="%.2f"
            )
            driver_rate = st.number_input(
                "Driver Rate (€/hour)",
                min_value=0.0,
                value=25.0,
                step=1.0,
                format="%.2f"
            )
        
        with col2:
            vehicle_rate = st.number_input(
                "Vehicle Rate (€/km)",
                min_value=0.0,
                value=0.5,
                step=0.1,
                format="%.2f"
            )
            overhead_rate = st.number_input(
                "Overhead Rate (%)",
                min_value=0.0,
                value=15.0,
                step=1.0,
                format="%.1f"
            )
    
    with st.expander("Cargo-Specific Settings"):
        temperature_control = st.checkbox(
            "Temperature Control Required",
            help="Enable for temperature-controlled cargo"
        )
        if temperature_control:
            temp_control_rate = st.number_input(
                "Temperature Control Cost (€/hour)",
                min_value=0.0,
                value=10.0,
                step=1.0,
                format="%.2f"
            )
        
        cleaning_required = st.checkbox(
            "Special Cleaning Required",
            help="Enable for cargo requiring special cleaning"
        )
        if cleaning_required:
            cleaning_rate = st.number_input(
                "Cleaning Cost (€)",
                min_value=0.0,
                value=100.0,
                step=10.0,
                format="%.2f"
            )
    
    return {
        "components": {
            "empty_driving": include_empty_driving,
            "tolls": include_tolls,
            "parking": include_parking,
            "cargo_insurance": include_cargo_insurance,
            "cleaning": include_cleaning,
            "overheads": include_overheads
        },
        "rates": {
            "fuel_price": fuel_price,
            "driver_rate": driver_rate,
            "vehicle_rate": vehicle_rate,
            "overhead_rate": overhead_rate
        },
        "cargo": {
            "temperature_control": temperature_control,
            "temperature_control_rate": temp_control_rate if temperature_control else None,
            "cleaning_required": cleaning_required,
            "cleaning_rate": cleaning_rate if cleaning_required else None
        }
    }
