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
    
    # Add container styling
    st.markdown("""
        <style>
        div[data-testid="stExpander"] {
            width: 100% !important;
            margin-bottom: 1rem !important;
        }
        div.row-widget.stRadio > div {
            width: 100% !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
        }
        div.element-container {
            width: 100% !important;
        }
        div[data-testid="metric-container"] {
            padding: 1rem;
            background: rgba(28, 131, 225, 0.1);
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        # Header with key metrics in a single row
        col1, col2, col3 = st.columns([2, 1, 1])
        
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
                offer.pickup_date.strftime("%Y-%m-%d")
            )
            offer_logger.debug("displayed_pickup_metric", pickup_date=offer.pickup_date.isoformat())
        
        with col3:
            st.metric(
                "Delivery",
                offer.delivery_date.strftime("%Y-%m-%d")
            )
            offer_logger.debug("displayed_delivery_metric", delivery_date=offer.delivery_date.isoformat())
        
        # Transport Details in a full-width expander
        with st.expander("Transport Details", expanded=True):
            cols = st.columns(2)
            with cols[0]:
                st.write("**Transport Type:**", offer.transport_type)
                st.write("**Base Cost:**", f"€{float(offer.base_cost):,.2f}")
                offer_logger.debug("displayed_transport_details", transport_type=offer.transport_type, base_cost=str(offer.base_cost))
            
            with cols[1]:
                st.write("**Cargo Type:**", offer.cargo_type)
                st.write("**Margin Amount:**", f"€{float(offer.margin_amount):,.2f}")
                offer_logger.debug("displayed_cargo_details", cargo_type=offer.cargo_type, margin_amount=str(offer.margin_amount))
        
        # Route Description in a full-width expander
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

def display_final_offer(offer_id: str):
    """Display the final offer after creation."""
    offer_logger = logger.bind(component="final_offer_display")
    
    try:
        # Get offer data from API
        api_client = st.session_state.api_client
        offer_data = api_client.get_offer(offer_id)
        
        st.header("Final Offer")
        
        # Display price and margin
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Final Price",
                f"€{float(offer_data['final_price']):,.2f}",
                delta=f"Margin: {float(offer_data['margin']):,.1f}%"
            )
        with col2:
            st.metric(
                "Base Cost",
                f"€{float(offer_data['total_cost']):,.2f}"
            )
        with col3:
            st.metric(
                "Margin Amount",
                f"€{float(offer_data['final_price'] - offer_data['total_cost']):,.2f}"
            )
        
        # Transport Details
        with st.expander("Transport Details", expanded=True):
            st.write(f"**Transport Type:** {offer_data.get('transport_type', 'Standard Truck')}")
            st.write(f"**Cargo Type:** {offer_data.get('cargo_type', 'General Cargo')}")
            
            # Display fun fact if available
            if 'fun_fact' in offer_data and offer_data['fun_fact']:
                st.info(f"**Did you know?** {offer_data['fun_fact']}")
        
        # Additional Services
        if offer_data.get('additional_services'):
            with st.expander("Additional Services"):
                for service in offer_data['additional_services']:
                    st.write(f"- {service}")
        
        # Notes
        if offer_data.get('notes'):
            with st.expander("Notes"):
                st.write(offer_data['notes'])
        
        # Add button to create new offer
        if st.button("Create New Offer", use_container_width=True):
            # Clear all relevant session state
            keys_to_clear = ['final_offer_id', 'offer_preview']
            for key in keys_to_clear:
                if hasattr(st.session_state, key):
                    delattr(st.session_state, key)
            st.rerun()
        
    except Exception as e:
        st.error("An error occurred while loading the offer")
        offer_logger.error("Error loading offer", error=str(e))
        traceback.print_exc()

def display_offer_preview(
    offer_settings: Dict,
    base_cost: Decimal,
    route_description: str,
    fun_fact: Optional[str] = None
):
    """Display a preview of the offer before finalizing."""
    offer_logger = logger.bind(component="offer_preview")
    
    # Calculate pricing
    margin_percentage = Decimal(str(offer_settings["margin_percentage"]))
    margin_amount = base_cost * (margin_percentage / Decimal("100"))
    final_price = base_cost + margin_amount
    
    # Create offer object for preview
    preview_offer = TransportOffer(
        id=str(uuid.uuid4()),
        price=final_price,
        base_cost=base_cost,
        margin_percentage=float(margin_percentage),
        pickup_date=st.session_state.get("pickup_time", datetime.now()),
        delivery_date=st.session_state.get("delivery_time", datetime.now()),
        transport_type=offer_settings["transport_type"],
        cargo_type=offer_settings["cargo_type"],
        route_description=route_description,
        fun_fact=fun_fact,
        additional_services=offer_settings["additional_services"],
        notes=offer_settings["notes"]
    )
    
    # Display the offer preview
    st.subheader("Offer Preview")
    display_offer(preview_offer)
    
    # Add action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "Send Offer to Client",
            key="send_offer",
            use_container_width=True,
            type="primary"
        ):
            try:
                # Prepare offer data
                offer_data = {
                    "route_id": st.session_state.get("current_route_id"),
                    "margin": float(margin_percentage),
                    "total_cost": float(base_cost),
                    "transport_type": offer_settings["transport_type"],
                    "cargo_type": offer_settings["cargo_type"],
                    "additional_services": offer_settings["additional_services"],
                    "notes": offer_settings["notes"] if offer_settings["notes"] else None,
                    "fun_fact": fun_fact
                }
                
                # Log the request
                offer_logger.info(
                    "sending_offer",
                    route_id=offer_data["route_id"],
                    margin=offer_data["margin"],
                    total_cost=offer_data["total_cost"]
                )
                
                # Send to API
                if not hasattr(st.session_state, "api_client"):
                    raise Exception("API client not initialized")
                
                response_data = st.session_state.api_client.create_offer(offer_data)
                
                # Store offer ID and clear preview
                if "id" in response_data:
                    st.session_state.final_offer_id = response_data["id"]
                    if hasattr(st.session_state, "offer_preview"):
                        delattr(st.session_state, "offer_preview")
                    
                    # Log success and rerun to show final offer
                    offer_logger.info(
                        "offer_created",
                        offer_id=response_data["id"],
                        final_price=response_data.get("final_price")
                    )
                    st.rerun()
                else:
                    raise Exception("Response missing offer ID")
                
            except Exception as e:
                offer_logger.error(
                    "offer_creation_failed", 
                    error=str(e),
                    response=str(response_data) if 'response_data' in locals() else None
                )
                st.error(f"Failed to create offer: {str(e)}")
                traceback.print_exc()
    
    with col2:
        if st.button(
            "Edit Offer",
            key="edit_offer",
            use_container_width=True
        ):
            if hasattr(st.session_state, "offer_preview"):
                delattr(st.session_state, "offer_preview")
            st.rerun()

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

def render_offer_generation():
    """Render the offer generation page."""
    offer_logger = logger.bind(component="offer_generation")
    
    # Log session state for debugging
    offer_logger.info(
        "session_state",
        has_route_id=hasattr(st.session_state, "current_route_id"),
        has_cost_data=hasattr(st.session_state, "cost_data"),
        has_final_offer=hasattr(st.session_state, "final_offer_id"),
        has_preview=hasattr(st.session_state, "offer_preview"),
        route_id=getattr(st.session_state, "current_route_id", None),
        final_offer_id=getattr(st.session_state, "final_offer_id", None)
    )

    # Initialize API client if needed
    if not hasattr(st.session_state, "api_client"):
        st.session_state.api_client = APIClient(
            base_url="http://localhost:5001",
            api_key="development"
        )
        offer_logger.info("api_client_initialized")

    if not hasattr(st.session_state, "current_route_id"):
        st.error("No route selected")
        return
        
    route_id = st.session_state.current_route_id
    
    # Get cost data if not already in session
    if not hasattr(st.session_state, "cost_data"):
        st.error("Cost data not available")
        return
        
    cost_data = st.session_state.cost_data
    base_cost = Decimal(str(cost_data.total_cost))
    
    # Display final offer if available
    if hasattr(st.session_state, "final_offer_id"):
        offer_logger.info("displaying_final_offer", offer_id=st.session_state.final_offer_id)
        display_final_offer(st.session_state.final_offer_id)
        return
    
    # Display offer form if no preview
    if not hasattr(st.session_state, "offer_preview"):
        offer_logger.info("rendering_offer_controls")
        offer_settings = render_offer_controls(base_cost)
        
        if offer_settings:
            # Generate route description
            route_description = f"Transport from {st.session_state.origin_address} to {st.session_state.destination_address}"
            
            # Store preview in session state
            st.session_state.offer_preview = {
                "settings": offer_settings,
                "base_cost": base_cost,
                "route_description": route_description
            }
            offer_logger.info("stored_offer_preview", settings=offer_settings)
            st.rerun()
            
    # Display preview if available
    else:
        offer_logger.info("displaying_offer_preview")
        preview_data = st.session_state.offer_preview
        
        # Get fun fact from API
        try:
            route_data = st.session_state.api_client.get_route(route_id)
            fun_fact = st.session_state.api_client.generate_fun_fact({"route": route_data}).get("fun_fact")
        except Exception as e:
            fun_fact = None
            offer_logger.error("Error generating fun fact", error=str(e))
        
        display_offer_preview(
            preview_data["settings"],
            preview_data["base_cost"],
            preview_data["route_description"],
            fun_fact=fun_fact
        )

def main():
    render_offer_generation()

if __name__ == "__main__":
    main()
