"""
Cost calculation component.
"""
import streamlit as st
from typing import Dict, Optional
from dataclasses import dataclass
from decimal import Decimal
import structlog

# Configure logging
logger = structlog.get_logger(__name__)

@dataclass
class EnhancedCostBreakdown:
    """Enhanced data class for detailed cost breakdown."""
    # Country-specific costs
    fuel_costs: Dict[str, Decimal]
    toll_costs: Dict[str, Decimal]
    driver_costs: Dict[str, Decimal]
    
    # Time-based costs
    rest_period_costs: Decimal
    loading_unloading_costs: Decimal
    
    # Empty driving costs per country
    empty_driving_costs: Dict[str, Dict[str, Decimal]]
    
    # Cargo-specific costs
    cargo_specific_costs: Dict[str, Decimal]
    
    # Overhead costs
    overheads: Dict[str, Decimal]
    
    # Metadata
    calculation_method: str
    is_final: bool
    version: str = "2.0"
    currency: str = "EUR"
    
    @property
    def total_fuel_cost(self) -> Decimal:
        """Calculate total fuel cost across all countries."""
        return sum(self.fuel_costs.values(), Decimal("0"))
    
    @property
    def total_toll_cost(self) -> Decimal:
        """Calculate total toll cost across all countries."""
        return sum(self.toll_costs.values(), Decimal("0"))
    
    @property
    def total_driver_cost(self) -> Decimal:
        """Calculate total driver cost across all countries."""
        return sum(self.driver_costs.values(), Decimal("0"))
    
    @property
    def total_empty_driving_cost(self) -> Decimal:
        """Calculate total empty driving cost."""
        total = Decimal("0")
        for country_costs in self.empty_driving_costs.values():
            total += sum(Decimal(str(cost)) for cost in country_costs.values())
        return total
    
    @property
    def total_cargo_cost(self) -> Decimal:
        """Calculate total cargo-specific cost."""
        return sum(self.cargo_specific_costs.values(), Decimal("0"))
    
    @property
    def total_overhead_cost(self) -> Decimal:
        """Calculate total overhead cost."""
        return sum(Decimal(str(v)) for v in self.overheads.values())
    
    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost including all components."""
        components = [
            self.total_fuel_cost,
            self.total_toll_cost,
            self.total_driver_cost,
            self.rest_period_costs,
            self.loading_unloading_costs,
            self.total_empty_driving_cost,
            self.total_cargo_cost,
            self.total_overhead_cost
        ]
        return sum(components, Decimal("0"))


def display_enhanced_cost_breakdown(cost_data: Optional[EnhancedCostBreakdown]):
    """Display a detailed breakdown of transportation costs.
    
    Args:
        cost_data: Cost breakdown data from the API
    """
    cost_logger = logger.bind(component="cost_breakdown")
    
    if cost_data is None:
        cost_logger.warning("No cost data available")
        st.warning("Cost calculation in progress...")
        return
        
    cost_logger.info("Displaying cost breakdown",
                total_cost=str(cost_data.total_cost),
                has_fuel_costs=bool(cost_data.fuel_costs),
                has_toll_costs=bool(cost_data.toll_costs),
                has_driver_costs=bool(cost_data.driver_costs))
    
    st.subheader("Cost Breakdown")
    
    # Log individual cost components
    cost_logger.info("Cost components",
                fuel_costs={k: str(v) for k, v in cost_data.fuel_costs.items()},
                toll_costs={k: str(v) for k, v in cost_data.toll_costs.items()},
                driver_costs={k: str(v) for k, v in cost_data.driver_costs.items()},
                rest_period_costs=str(cost_data.rest_period_costs),
                loading_unloading_costs=str(cost_data.loading_unloading_costs),
                empty_driving_costs={k: {sk: str(sv) for sk, sv in v.items()}
                                   for k, v in cost_data.empty_driving_costs.items()},
                cargo_specific_costs={k: str(v) for k, v in cost_data.cargo_specific_costs.items()},
                overheads={k: str(v) for k, v in cost_data.overheads.items()})
    
    # Distance-Based Costs
    with st.expander("Distance-Based Costs", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fuel_cost = float(cost_data.total_fuel_cost)
            cost_logger.info("Displaying fuel cost", value=str(fuel_cost))
            st.metric("Fuel Cost", f"€{fuel_cost:,.2f}")
        with col2:
            toll_cost = float(cost_data.total_toll_cost)
            cost_logger.info("Displaying toll cost", value=str(toll_cost))
            st.metric("Toll Cost", f"€{toll_cost:,.2f}")
        with col3:
            maintenance_cost = float(Decimal(str(cost_data.overheads.get('maintenance', '0'))))
            cost_logger.info("Displaying maintenance cost", value=str(maintenance_cost))
            st.metric("Maintenance Cost", f"€{maintenance_cost:,.2f}")
    
    # Time-Based Costs
    with st.expander("Time-Based Costs", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            driver_cost = float(cost_data.total_driver_cost)
            cost_logger.info("Displaying driver cost", value=str(driver_cost))
            st.metric("Driver Cost", f"€{driver_cost:,.2f}")
        with col2:
            rest_cost = float(cost_data.rest_period_costs)
            cost_logger.info("Displaying rest period cost", value=str(rest_cost))
            st.metric("Rest Period Cost", f"€{rest_cost:,.2f}")
        with col3:
            loading_cost = float(cost_data.loading_unloading_costs)
            cost_logger.info("Displaying loading/unloading cost", value=str(loading_cost))
            st.metric("Loading/Unloading", f"€{loading_cost:,.2f}")
    
    # Empty Driving Costs
    with st.expander("Empty Driving Costs", expanded=True):
        empty_cost = float(cost_data.total_empty_driving_cost)
        cost_logger.info("Displaying empty driving cost", value=str(empty_cost))
        st.metric("Empty Driving Total", f"€{empty_cost:,.2f}")
        
        # Show breakdown by country if available
        if cost_data.empty_driving_costs:
            st.write("Breakdown by Country:")
            for country, costs in cost_data.empty_driving_costs.items():
                country_total = sum(float(Decimal(str(v))) for v in costs.values())
                cost_logger.info(f"Empty driving cost for {country}", value=str(country_total))
                st.write(f"{country}: €{country_total:,.2f}")
    
    # Additional Costs
    with st.expander("Additional Costs", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            cargo_cost = float(cost_data.total_cargo_cost)
            cost_logger.info("Displaying cargo cost", value=str(cargo_cost))
            st.metric("Cargo-Specific", f"€{cargo_cost:,.2f}")
        with col2:
            overhead_cost = float(cost_data.total_overhead_cost)
            cost_logger.info("Displaying overhead cost", value=str(overhead_cost))
            st.metric("Overheads", f"€{overhead_cost:,.2f}")
    
    # Total Cost
    total_cost = float(cost_data.total_cost)
    cost_logger.info("Displaying total cost", value=str(total_cost))
    st.metric("Total Transportation Cost", f"€{total_cost:,.2f}", delta=None)


def render_cost_settings():
    """Render enhanced cost calculation settings and controls."""
    st.subheader("Cost Settings")
    
    with st.expander("Cost Components", expanded=True):
        st.markdown("#### Cost Calculation Options")
        col1, col2 = st.columns(2)
        
        with col1:
            include_empty_driving = st.checkbox(
                "Include Empty Driving",
                value=True,
                help="Calculate costs for return journey without cargo"
            )
            include_country_breakdown = st.checkbox(
                "Show Country Breakdown",
                value=True,
                help="Display costs broken down by country"
            )
            include_time_costs = st.checkbox(
                "Include Time-Based Costs",
                value=True,
                help="Calculate rest periods and loading/unloading costs"
            )
        
        with col2:
            include_cargo_costs = st.checkbox(
                "Include Cargo-Specific Costs",
                value=True,
                help="Calculate costs based on cargo type and requirements"
            )
            include_overheads = st.checkbox(
                "Include Business Overheads",
                value=True,
                help="Add fixed and variable overhead costs"
            )
            show_preliminary = st.checkbox(
                "Show Preliminary Costs",
                value=True,
                help="Display non-final cost calculations"
            )
    
    with st.expander("Calculation Method"):
        calculation_method = st.radio(
            "Select calculation method",
            ["standard", "detailed", "estimated"],
            help="Choose how detailed the cost calculation should be"
        )
        
        if calculation_method == "detailed":
            st.info(
                "Detailed calculation includes all cost components and "
                "country-specific breakdowns. This may take longer to compute."
            )
        elif calculation_method == "estimated":
            st.warning(
                "Estimated calculation uses simplified models and average rates. "
                "Results may be less accurate but are computed faster."
            )
    
    return {
        "include_empty_driving": include_empty_driving,
        "include_country_breakdown": include_country_breakdown,
        "include_time_costs": include_time_costs,
        "include_cargo_costs": include_cargo_costs,
        "include_overheads": include_overheads,
        "show_preliminary": show_preliminary,
        "calculation_method": calculation_method
    }
