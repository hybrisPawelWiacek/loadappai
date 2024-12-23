"""
LoadApp.AI Streamlit Frontend Application
"""
import streamlit as st
from datetime import datetime, timezone
from typing import List
import structlog

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
    render_offer_controls, display_offer_preview
)
from src.frontend.integration import submit_route, get_route_cost
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
if "api_client" not in st.session_state:
    logger.info("Initializing API client")
    st.session_state.api_client = APIClient(
        base_url="http://localhost:5001",
        api_key="development"
    )
    logger.info("API client initialized")

if "route_segments" not in st.session_state:
    st.session_state.route_segments = None
if "pickup_time" not in st.session_state:
    st.session_state.pickup_time = None
if "route_id" not in st.session_state:
    st.session_state.route_id = None
if "cost_data" not in st.session_state:
    st.session_state.cost_data = None
if "show_offer_form" not in st.session_state:
    st.session_state.show_offer_form = False
if "current_route_id" not in st.session_state:
    st.session_state.current_route_id = None
if "offer_preview" not in st.session_state:
    st.session_state.offer_preview = None

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stAlert {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .route-details {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #ccc;
    }
    </style>
    """, unsafe_allow_html=True)

def display_route_details(segments: List[RouteSegment], pickup_time: datetime):
    """Display route details including map, timeline, and metrics."""
    st.header("Route Details")
    
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

def main():
    """Main application entry point."""
    st.title("LoadApp.AI - Route Planning")
    
    # Create main form section
    st.header("Create New Route")
    
    # Render the route form and handle submission
    form_data = render_route_form()
    
    if form_data:
        with st.spinner("Calculating route..."):
            try:
                # Submit route and get segments
                segments, pickup_time, route_id = submit_route(form_data)
                
                # Update session state
                st.session_state.route_segments = segments
                st.session_state.pickup_time = pickup_time
                st.session_state.route_id = route_id
                st.session_state.current_route_id = route_id
                st.session_state.show_offer_form = False  # Reset offer form state
                st.session_state.offer_preview = None  # Reset offer preview
                
                # Get route cost calculation
                if st.session_state.route_id:
                    with st.spinner("Calculating costs..."):
                        cost_data = get_route_cost(st.session_state.route_id)
                        if cost_data:
                            st.session_state.cost_data = cost_data
                            st.success("Route and costs calculated successfully!")
                        else:
                            st.warning("Route calculated but cost calculation failed.")
                else:
                    st.success("Route calculated successfully!")
                
            except Exception as e:
                st.error(f"Error calculating route: {str(e)}")
    
    # Display route details if available
    if st.session_state.route_segments:
        with st.container():
            st.header("Route Details", anchor=False)
            display_route_details(st.session_state.route_segments, st.session_state.pickup_time)
        
        # Display cost breakdown if available
        if st.session_state.cost_data:
            with st.container():
                st.header("Cost Breakdown", anchor=False)
                display_enhanced_cost_breakdown(st.session_state.cost_data)
            
            # Show offer generation section
            with st.container():
                st.header("Generate Offer", anchor=False)
                
                # Add a button to show/hide the offer form
                if not st.session_state.show_offer_form:
                    if st.button("Create New Offer", key="create_offer_btn"):
                        st.session_state.show_offer_form = True
                        st.session_state.offer_preview = None
                        st.experimental_rerun()
                else:
                    if st.button("Cancel", key="cancel_offer_btn"):
                        st.session_state.show_offer_form = False
                        st.session_state.offer_preview = None
                        st.experimental_rerun()
                
                # Only show the offer form if the button has been clicked
                if st.session_state.show_offer_form:
                    st.divider()
                    offer_settings = render_offer_controls(base_cost=st.session_state.cost_data.total_cost)
                    
                    if offer_settings and not st.session_state.get("offer_preview"):
                        # Get route description from segments
                        route_description = f"Transport from {st.session_state.route_segments[0].start_location.address} to {st.session_state.route_segments[-1].end_location.address}"
                        
                        # Store offer preview in session state
                        st.session_state.offer_preview = {
                            "settings": offer_settings,
                            "base_cost": st.session_state.cost_data.total_cost,
                            "route_description": route_description
                        }
                        st.experimental_rerun()
                    
                    # Display offer preview if available
                    if st.session_state.get("offer_preview"):
                        preview = st.session_state.offer_preview
                        display_offer_preview(
                            offer_settings=preview["settings"],
                            base_cost=preview["base_cost"],
                            route_description=preview["route_description"]
                        )

if __name__ == "__main__":
    main()
