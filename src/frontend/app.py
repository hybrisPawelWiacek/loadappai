"""
LoadApp.AI Streamlit Frontend Application
"""
import streamlit as st
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import structlog
from decimal import Decimal

from src.frontend.components.route_form import (
    RouteFormData, render_route_form, display_route_summary, Location
)
from src.frontend.components.map_visualization import (
    create_route_map, display_route_timeline, RouteSegment, TimelineEventType
)
from src.frontend.components.cost_calculation import (
    display_enhanced_cost_breakdown, EnhancedCostBreakdown
)
from src.frontend.components.offer_generation import (
    render_offer_controls, display_offer_preview, display_offer
)
from src.frontend.api_client import APIClient

# Configure logging
logger = structlog.get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="LoadApp.AI - Route Planning",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if not hasattr(st.session_state, "api_client"):
    st.session_state.api_client = APIClient(
        base_url="http://localhost:5001",
        api_key="development"
    )

# Initialize other session state variables if not present
session_vars = {
    "route_segments": None,
    "pickup_time": None,
    "route_id": None,
    "cost_data": None,
    "show_offer_form": False,
    "current_route_id": None,
    "offer_preview": None,
    "error_state": None,
    "last_successful_operation": None,
    "final_offer": None,
    "api_client": None
}

for var, default in session_vars.items():
    if not hasattr(st.session_state, var):
        setattr(st.session_state, var, default)
        logger.info(f"Initialized session state variable: {var}")

# Custom styling
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Alert styling */
    .stAlert {
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid;
    }
    .element-container:has(div.stAlert) {
        margin: 1rem 0;
    }
    
    /* Section styling */
    .route-details, .cost-breakdown, .offer-section {
        margin: 2rem 0;
        padding: 1.5rem;
        background: #f8f9fa;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        width: 100%;
    }
    
    /* Form styling */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 4px;
    }
    
    /* Metric styling */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Map container styling */
    .element-container:has(iframe) {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Final Offer styling */
    [data-testid="stExpander"] {
        width: 100%;
        margin-bottom: 1rem;
    }

    .element-container {
        width: 100%;
    }

    .block-container {
        max-width: 1200px;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Ensure consistent width for metrics */
    [data-testid="metric-container"] {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def display_route_details(segments: List[RouteSegment], pickup_time: datetime):
    """Display route details including map, timeline, and metrics."""
    if not segments:
        st.error("No route segments available")
        return
        
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    total_distance = sum(s.distance_km for s in segments)
    total_duration = sum(s.duration_hours for s in segments)
    empty_distance = sum(s.distance_km for s in segments if s.is_empty_driving)
    
    with col1:
        st.metric("Total Distance", f"{total_distance:.1f} km")
    with col2:
        st.metric("Total Duration", f"{total_duration:.1f} hours")
    with col3:
        st.metric("Empty Driving", f"{empty_distance:.1f} km")
    
    # Display map
    st.subheader("Route Map")
    create_route_map(segments, key="route_map")
    
    # Display timeline
    st.subheader("Route Timeline")
    display_route_timeline(segments, pickup_time)

def handle_route_submission(form_data: RouteFormData) -> Optional[Tuple[List[RouteSegment], datetime, str]]:
    """Handle route form submission."""
    try:
        logger.info("Submitting route", form_data=form_data)
        # Submit route using API client
        segments, pickup_time, route_id = st.session_state.api_client.submit_route(form_data)
        
        # Display route details first
        st.session_state.route_segments = segments
        st.session_state.pickup_time = pickup_time
        st.session_state.route_id = route_id
        
        # Display route visualization and timeline
        display_route_details(segments, pickup_time)
        
        # Then calculate costs asynchronously
        with st.spinner("Calculating route costs..."):
            logger.info("Calculating costs for route", route_id=route_id)
            cost_data = st.session_state.api_client.get_route_cost(route_id)
            if cost_data:
                st.session_state.cost_data = cost_data
                logger.info("Cost calculation successful", total_cost=str(cost_data.total_cost))
                # Display cost breakdown after calculation
                display_enhanced_cost_breakdown(cost_data)
            else:
                logger.warning("Cost calculation failed")
                st.error("Failed to calculate costs for the route")
            
        return segments, pickup_time, route_id
        
    except Exception as e:
        logger.error("Error submitting route", error=str(e))
        st.error(f"Error submitting route: {str(e)}")
        return None

def main():
    """Main application entry point."""
    st.title("LoadApp.AI - Route Planning")
    
    # Initialize API client if not already done
    if not hasattr(st.session_state, "api_client"):
        st.session_state.api_client = APIClient(
            base_url="http://localhost:5001",
            api_key="development"
        )
        logger.info("API client initialized")
    
    # Create containers for each section
    form_container = st.container()
    route_container = st.container()
    cost_container = st.container()
    offer_container = st.container()
    
    # Always render the route form in the form container
    with form_container:
        form_data = render_route_form()
        if form_data:
            # Handle form submission
            result = handle_route_submission(form_data)
            if result:
                segments, pickup_time, route_id = result
                st.success("Route calculated successfully!")
                st.experimental_rerun()
    
    # Display route details if we have data
    with route_container:
        if (hasattr(st.session_state, "route_segments") and 
            hasattr(st.session_state, "pickup_time") and 
            getattr(st.session_state, "route_segments") is not None):
            
            segments = st.session_state.route_segments
            pickup_time = st.session_state.pickup_time
            display_route_details(segments, pickup_time)
    
    # Display cost breakdown in a separate container
    with cost_container:
        if hasattr(st.session_state, "cost_data") and st.session_state.cost_data is not None:
            st.subheader("Cost Breakdown")
            display_enhanced_cost_breakdown(st.session_state.cost_data)
            st.session_state.show_offer_form = True
    
    # Show offer generation form in its own container
    with offer_container:
        if st.session_state.show_offer_form:
            # Show offer generation form
            offer_data = render_offer_controls(base_cost=st.session_state.cost_data.total_cost)
            
            if offer_data:
                # Store offer preview data in session state
                st.session_state.offer_preview = {
                    **offer_data,
                    "base_cost": st.session_state.cost_data.total_cost,
                    "route_description": f"Transport from {segments[0].start_location.address} to {segments[-1].end_location.address}"
                }
                st.experimental_rerun()
            
            # Display final offer if it exists
            if hasattr(st.session_state, "final_offer"):
                st.header("Final Offer")
                display_offer(st.session_state.final_offer)
                
                # Add button to create new offer
                if st.button("Create New Offer"):
                    for key in ["route_segments", "pickup_time", "current_route_id", 
                              "cost_data", "final_offer", "offer_preview"]:
                        if hasattr(st.session_state, key):
                            delattr(st.session_state, key)
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
