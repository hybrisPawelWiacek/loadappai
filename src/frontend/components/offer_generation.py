"""
Offer generation component for LoadApp.AI
"""
import uuid
import streamlit as st
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import structlog
import traceback
import requests
from src.frontend.api_client import APIClient

# Configure logging
logger = structlog.get_logger(__name__)

@dataclass
class TransportOffer:
    """Data class for transport offers."""
    id: str
    price: Decimal
    base_cost: Decimal
    margin_percentage: float
    pickup_date: datetime
    delivery_date: datetime
    transport_type: str
    cargo_type: str
    route_description: str
    fun_fact: Optional[str] = None
    additional_services: Optional[List[str]] = None
    notes: Optional[str] = None
    
    @property
    def margin_amount(self) -> Decimal:
        """Calculate the margin amount."""
        return self.price - self.base_cost

def display_offer(offer: TransportOffer):
    """Display a single transport offer.
    
    Args:
        offer: The transport offer to display
    """
    offer_logger = logger.bind(
        component="offer_display",
        offer_id=offer.id,
        transport_type=offer.transport_type,
        cargo_type=offer.cargo_type
    )
    offer_logger.info("displaying_offer", price=str(offer.price), margin=str(offer.margin_amount))
    
    with st.container():
        # Header with key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Final Price",
                f"€{float(offer.price):,.2f}",
                delta=f"Margin: {offer.margin_percentage:.1f}%"
            )
            offer_logger.debug("displayed_price_metric", price=str(offer.price), margin_percentage=offer.margin_percentage)
        
        with col2:
            st.metric(
                "Pickup",
                offer.pickup_date.strftime("%Y-%m-%d %H:%M")
            )
            offer_logger.debug("displayed_pickup_metric", pickup_date=offer.pickup_date.isoformat())
        
        with col3:
            st.metric(
                "Delivery",
                offer.delivery_date.strftime("%Y-%m-%d %H:%M")
            )
            offer_logger.debug("displayed_delivery_metric", delivery_date=offer.delivery_date.isoformat())
        
        # Detailed sections
        with st.expander("Transport Details", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Transport Type:**", offer.transport_type)
                st.write("**Base Cost:**", f"€{float(offer.base_cost):,.2f}")
                offer_logger.debug("displayed_transport_details", transport_type=offer.transport_type, base_cost=str(offer.base_cost))
            
            with col2:
                st.write("**Cargo Type:**", offer.cargo_type)
                st.write("**Margin Amount:**", f"€{float(offer.margin_amount):,.2f}")
                offer_logger.debug("displayed_cargo_details", cargo_type=offer.cargo_type, margin_amount=str(offer.margin_amount))
        
        # Route description
        with st.expander("Route Description", expanded=True):
            st.write(offer.route_description)
            offer_logger.debug("displayed_route_description", route_description=offer.route_description)
            
            if offer.fun_fact:
                st.info(f"**Did you know?** {offer.fun_fact}")
                offer_logger.debug("displayed_fun_fact", fun_fact=offer.fun_fact)
        
        # Additional services if any
        if offer.additional_services:
            with st.expander("Additional Services"):
                for service in offer.additional_services:
                    st.write(f"- {service}")
                offer_logger.debug("displayed_additional_services", services=offer.additional_services)
        
        # Notes if any
        if offer.notes:
            with st.expander("Notes"):
                st.write(offer.notes)
                offer_logger.debug("displayed_notes", notes=offer.notes)
        
        st.markdown("---")

def render_offer_controls(base_cost: Optional[Decimal] = None):
    """Render offer generation controls and settings.
    
    Args:
        base_cost: Optional base cost to calculate margins
    """
    offer_logger = logger.bind(component="offer_controls")
    offer_logger.info("rendering_offer_controls", base_cost=str(base_cost) if base_cost else None)
    
    with st.form(key=f"offer_form_{st.session_state.get('current_route_id', 'default')}"):
        # Pricing section
        st.write("### Pricing")
        col1, col2 = st.columns(2)
        
        with col1:
            if base_cost is not None:
                st.write(f"**Base Cost:** €{float(base_cost):,.2f}")
            margin_percentage = st.slider(
                "Margin Percentage",
                min_value=0.0,
                max_value=50.0,
                value=15.0,
                step=0.5,
                help="Percentage markup over base cost"
            )
            offer_logger.debug("margin_slider_value", margin_percentage=margin_percentage)
            
        with col2:
            if base_cost is not None:
                margin_amount = base_cost * (Decimal(str(margin_percentage)) / Decimal("100"))
                final_price = base_cost + margin_amount
                st.write(f"**Margin Amount:** €{float(margin_amount):,.2f}")
                st.write(f"**Final Price:** €{float(final_price):,.2f}")
                offer_logger.debug("calculated_prices", margin_amount=str(margin_amount), final_price=str(final_price))
        
        # Transport details
        st.write("### Transport Details")
        col1, col2 = st.columns(2)
        
        with col1:
            transport_type = st.selectbox(
                "Transport Type",
                options=["Standard Truck", "Refrigerated Truck", "Heavy Load Truck"],
                index=0,
                key="transport_type"
            )
            offer_logger.debug("transport_type_selected", transport_type=transport_type)
            
        with col2:
            cargo_type = st.selectbox(
                "Cargo Type",
                options=["General Cargo", "Temperature Controlled", "Heavy Machinery"],
                index=0,
                key="cargo_type"
            )
            offer_logger.debug("cargo_type_selected", cargo_type=cargo_type)
        
        # Additional services
        st.write("### Additional Services")
        col1, col2 = st.columns(2)
        
        with col1:
            realtime_tracking = st.checkbox("Real-time Tracking", key="realtime_tracking")
            insurance = st.checkbox("Insurance Coverage", key="insurance")
                
        with col2:
            express = st.checkbox("Express Delivery", key="express")
            support = st.checkbox("24/7 Support", key="support")
        
        additional_services = []
        if realtime_tracking:
            additional_services.append("Real-time Tracking")
        if insurance:
            additional_services.append("Insurance Coverage")
        if express:
            additional_services.append("Express Delivery")
        if support:
            additional_services.append("24/7 Support")
        
        offer_logger.debug("additional_services_selected", services=additional_services)
        
        # Notes
        notes = st.text_area(
            "Additional Notes",
            placeholder="Enter any additional notes or special requirements...",
            key="notes"
        )
        if notes:
            offer_logger.debug("notes_added", notes=notes)
        
        # Submit button
        submitted = st.form_submit_button("Preview Offer")
        
        if submitted:
            offer_logger.info("offer_form_submitted")
            if base_cost is None:
                offer_logger.error("missing_base_cost")
                st.error("Base cost is required to generate an offer")
                return None
            
            offer_data = {
                "margin_percentage": margin_percentage,
                "transport_type": transport_type,
                "cargo_type": cargo_type,
                "additional_services": additional_services,
                "notes": notes if notes else None
            }
            offer_logger.info("offer_data_prepared", **offer_data)
            return offer_data
    
    return None

def display_offer_preview(
    offer_settings: Dict,
    base_cost: Decimal,
    route_description: str,
    fun_fact: Optional[str] = None
):
    """Display a preview of the offer before finalizing.
    
    Args:
        offer_settings: Settings from render_offer_controls
        base_cost: Base cost for the transport
        route_description: Description of the route
        fun_fact: Optional fun fact about the route
    """
    offer_logger = logger.bind(
        component="offer_preview",
        route_id=st.session_state.get("current_route_id")
    )
    offer_logger.info(
        "displaying_offer_preview",
        base_cost=str(base_cost),
        margin_percentage=offer_settings["margin_percentage"]
    )
    
    try:
        # Calculate pricing
        margin_percentage = Decimal(str(offer_settings["margin_percentage"]))
        margin_amount = base_cost * (margin_percentage / Decimal("100"))
        final_price = base_cost + margin_amount
        
        offer_logger.debug(
            "calculated_offer_prices",
            margin_amount=str(margin_amount),
            final_price=str(final_price)
        )
        
        # Create offer object for preview
        offer = TransportOffer(
            id=str(uuid.uuid4()),
            price=final_price,
            base_cost=base_cost,
            margin_percentage=float(margin_percentage),
            pickup_date=datetime.now(),
            delivery_date=datetime.now() + timedelta(days=2),
            transport_type=offer_settings["transport_type"],
            cargo_type=offer_settings["cargo_type"],
            route_description=route_description,
            fun_fact=fun_fact,
            additional_services=offer_settings["additional_services"],
            notes=offer_settings["notes"]
        )
        
        offer_logger.info(
            "created_offer_preview",
            offer_id=offer.id,
            price=str(offer.price),
            transport_type=offer.transport_type
        )
        
        # Display the offer preview
        display_offer(offer)
        
        # Add action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Send Offer to Client", key="send_offer"):
                try:
                    # Ensure API client is initialized
                    if "api_client" not in st.session_state:
                        offer_logger.warning("api_client_missing_reinitializing")
                        st.session_state.api_client = APIClient(
                            base_url="http://localhost:5001",
                            api_key="development"
                        )
                        offer_logger.info("api_client_reinitialized")
                    
                    # Prepare offer data for API
                    offer_data = {
                        "route_id": st.session_state.get("current_route_id"),
                        "margin": float(margin_percentage),
                        "total_cost": float(base_cost),  # Include the base cost
                        "transport_type": offer_settings["transport_type"],
                        "cargo_type": offer_settings["cargo_type"],
                        "additional_services": offer_settings["additional_services"],
                        "notes": offer_settings["notes"] if offer_settings["notes"] else None
                    }
                    
                    offer_logger.info(
                        "sending_offer_to_api",
                        offer_id=offer.id,
                        route_id=offer_data["route_id"],
                        offer_data=offer_data
                    )
                    
                    # Create offer via API
                    response = st.session_state.api_client.create_offer(offer_data)
                    
                    offer_logger.info(
                        "offer_created_successfully",
                        api_offer_id=response.get("id"),
                        status=response.get("status")
                    )
                    
                    st.success("Offer created successfully!")
                    
                    # Create TransportOffer object from API response
                    final_offer = TransportOffer(
                        id=response["id"],
                        price=Decimal(str(response["final_price"])),
                        base_cost=Decimal(str(response["total_cost"])),
                        margin_percentage=float(response["margin"]),
                        pickup_date=st.session_state.get("pickup_time", datetime.now()),
                        delivery_date=st.session_state.get("delivery_time", datetime.now()),
                        transport_type=offer_settings["transport_type"],
                        cargo_type=offer_settings["cargo_type"],
                        route_description=response.get("description", "Route description not available"),
                        fun_fact=response.get("fun_fact"),
                        additional_services=offer_settings["additional_services"],
                        notes=offer_settings["notes"]
                    )
                    
                    # Store final offer in session state and display it
                    st.session_state.final_offer = final_offer
                    st.subheader("Final Offer")
                    display_offer(final_offer)
                    
                    # Hide the offer form
                    st.session_state.show_offer_form = False
                    
                except Exception as e:
                    error_msg = str(e)
                    offer_logger.error(
                        "error_sending_offer",
                        error=error_msg,
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc()
                    )
                    st.error(f"Error sending offer: {error_msg}")
        
        with col2:
            if st.button("Edit Offer", key="edit_offer"):
                offer_logger.info("editing_offer", offer_id=offer.id)
                st.session_state.offer_preview = None
                
    except Exception as e:
        error_msg = str(e)
        offer_logger.error(
            "error_displaying_preview",
            error=error_msg,
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        st.error(f"Error displaying offer preview: {error_msg}")

def render_offer_generation():
    """Render the offer generation page."""
    offer_logger = logger.bind(component="offer_generation")
    offer_logger.info("rendering_offer_generation")
    
    # Ensure API client is initialized
    if "api_client" not in st.session_state:
        offer_logger.warning("api_client_missing_reinitializing")
        st.session_state.api_client = APIClient(
            base_url="http://localhost:5001",
            api_key="development"
        )
        offer_logger.info("api_client_reinitialized")
    
    # Get the route ID from session state
    route_id = st.session_state.get("current_route_id")
    if not route_id:
        offer_logger.error("route_id_not_found")
        st.error("No route selected. Please go back and select a route.")
        return
    
    # Get the base cost from session state
    base_cost = st.session_state.get("base_cost")
    
    # Render offer controls
    offer_settings = render_offer_controls(base_cost)
    
    if offer_settings:
        # Get the route description from session state
        route_description = st.session_state.get("route_description")
        fun_fact = st.session_state.get("fun_fact")
        
        # Display offer preview
        display_offer_preview(offer_settings, base_cost, route_description, fun_fact)

def main():
    render_offer_generation()

if __name__ == "__main__":
    main()
