"""
Route input form component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RouteFormData:
    """Data class for route form inputs."""
    origin: str
    destination: str
    transport_type: str
    cargo_type: str
    additional_notes: Optional[str] = None

def render_route_form() -> Optional[RouteFormData]:
    """Render the route input form.
    
    Returns:
        RouteFormData if form is submitted successfully, None otherwise
    """
    with st.form("route_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            origin = st.text_input(
                "Origin Address",
                placeholder="Enter pickup location"
            )
            
            transport_type = st.selectbox(
                "Transport Type",
                ["Truck", "Van", "Container"],
                help="Select the type of transport needed"
            )
        
        with col2:
            destination = st.text_input(
                "Destination Address",
                placeholder="Enter delivery location"
            )
            
            cargo_type = st.selectbox(
                "Cargo Type",
                ["General", "Temperature Controlled", "Hazardous", "Bulk"],
                help="Select the type of cargo being transported"
            )
        
        additional_notes = st.text_area(
            "Additional Notes",
            placeholder="Any special requirements or instructions...",
            help="Optional: Add any special requirements or notes about the route"
        )
        
        submitted = st.form_submit_button("Calculate Route", type="primary")
        
        if submitted:
            if not origin or not destination:
                st.error("Please enter both origin and destination addresses.")
                return None
                
            return RouteFormData(
                origin=origin,
                destination=destination,
                transport_type=transport_type,
                cargo_type=cargo_type,
                additional_notes=additional_notes if additional_notes else None
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
        st.write(route_data.origin)
        st.markdown("**Transport Type**")
        st.write(route_data.transport_type)
    
    with col2:
        st.markdown("**Destination**")
        st.write(route_data.destination)
        st.markdown("**Cargo Type**")
        st.write(route_data.cargo_type)
    
    if route_data.additional_notes:
        st.markdown("**Additional Notes**")
        st.write(route_data.additional_notes)
