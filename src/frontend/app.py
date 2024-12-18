"""
LoadApp.AI Streamlit Frontend Application
"""
import streamlit as st
from typing import Dict, Optional
import requests
from decimal import Decimal

from src.domain.value_objects import Location
from src.config import get_settings
from src.frontend.components import (
    render_route_form,
    display_route_summary,
    display_cost_breakdown,
    render_cost_settings,
    display_offer,
    render_offer_controls,
    display_offer_preview,
    render_settings_management,
    create_route_map,
    display_route_timeline,
    RouteSegment
)

settings = get_settings()

# Page configuration
st.set_page_config(
    page_title="LoadApp.AI - Smart Route Planning",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stTabs {
        margin-top: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application entry point."""
    st.title("LoadApp.AI 🚛")
    st.subheader("Smart Route Planning & Cost Calculation")
    
    # Initialize session state
    if "route_data" not in st.session_state:
        st.session_state["route_data"] = None
    if "cost_data" not in st.session_state:
        st.session_state["cost_data"] = None
    if "offer_data" not in st.session_state:
        st.session_state["offer_data"] = None
    
    # Sidebar with settings
    with st.sidebar:
        st.header("Quick Settings")
        transport_type = st.selectbox(
            "Transport Type",
            ["Truck", "Van", "Container"]
        )
        cargo_type = st.selectbox(
            "Cargo Type",
            ["General", "Temperature Controlled", "Hazardous", "Bulk"]
        )
        
        if st.button("Open Settings", type="secondary"):
            st.session_state["show_settings"] = True
    
    # Show settings modal if requested
    if st.session_state.get("show_settings", False):
        with st.expander("Settings", expanded=True):
            render_settings_management()
            if st.button("Close Settings"):
                st.session_state["show_settings"] = False
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["Route Planning", "Cost Calculation", "Offers"])
    
    with tab1:
        st.header("Route Planning")
        route_data = render_route_form()
        
        if route_data:
            with st.spinner("Processing route..."):
                try:
                    # TODO: Make API call to process route
                    # For now, using dummy data
                    segments = [
                        RouteSegment(
                            start_location=(52.5200, 13.4050),
                            end_location=(52.5200, 13.8050),
                            distance_km=200.0,
                            duration_hours=4.0,
                            is_empty_driving=True,
                            country="Germany"
                        ),
                        RouteSegment(
                            start_location=(52.5200, 13.8050),
                            end_location=(50.0755, 14.4378),
                            distance_km=350.0,
                            duration_hours=5.0,
                            country="Czech Republic"
                        )
                    ]
                    
                    # Display route visualization
                    create_route_map(segments)
                    display_route_timeline(segments)
                    
                    # Store route data
                    st.session_state["route_data"] = route_data
                    st.success("Route calculated successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing route: {str(e)}")
    
    with tab2:
        st.header("Cost Calculation")
        cost_settings = render_cost_settings()
        
        if st.session_state.get("route_data"):
            with st.spinner("Calculating costs..."):
                try:
                    # TODO: Make API call to calculate costs
                    # For now, using dummy data
                    cost_data = CostBreakdown(
                        base_cost=Decimal("500.00"),
                        fuel_cost_loaded=Decimal("300.00"),
                        fuel_cost_empty=Decimal("200.00"),
                        driver_wages=Decimal("400.00"),
                        vehicle_costs=Decimal("250.00"),
                        toll_cost=Decimal("150.00"),
                        parking_cost=Decimal("50.00"),
                        cargo_insurance=Decimal("100.00"),
                        cleaning_cost=Decimal("75.00"),
                        leasing_cost=Decimal("200.00"),
                        depreciation=Decimal("150.00"),
                        insurance_cost=Decimal("100.00"),
                        overhead_cost=Decimal("200.00")
                    )
                    
                    display_cost_breakdown(cost_data)
                    st.session_state["cost_data"] = cost_data
                    
                except Exception as e:
                    st.error(f"Error calculating costs: {str(e)}")
        else:
            st.info("Please calculate a route first in the Route Planning tab.")
    
    with tab3:
        st.header("Offers")
        
        if st.session_state.get("cost_data"):
            offer_settings = render_offer_controls(
                base_cost=st.session_state["cost_data"].total_cost
            )
            
            if offer_settings:
                with st.spinner("Generating offer..."):
                    try:
                        # TODO: Make API call to generate fun fact
                        fun_fact = "The route between Berlin and Prague follows an ancient trade route known as the 'Salt Road', which was used to transport salt from the Baltic Sea to Bohemia during medieval times."
                        
                        # Display offer preview
                        display_offer_preview(
                            offer_settings=offer_settings,
                            base_cost=st.session_state["cost_data"].total_cost,
                            route_description="Transport from Berlin to Prague via A13 and D8 highways",
                            fun_fact=fun_fact if offer_settings["fun_fact"] else None
                        )
                        
                        if st.session_state.get("offer_finalized"):
                            st.success("Offer finalized successfully!")
                            # TODO: Save offer to database
                            
                    except Exception as e:
                        st.error(f"Error generating offer: {str(e)}")
        else:
            st.info("Please calculate route costs first in the Cost Calculation tab.")

if __name__ == "__main__":
    main()
