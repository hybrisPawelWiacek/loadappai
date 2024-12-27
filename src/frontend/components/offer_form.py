"""
Offer creation and editing form component for LoadApp.AI
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

import streamlit as st
from streamlit import session_state as state

from src.domain.entities.offer import Offer
from src.domain.services import OfferGenerationService
from src.infrastructure.logging import get_logger

def render_offer_form(
    offer: Optional[Offer] = None,
    base_cost: Optional[Decimal] = None,
    route_description: Optional[str] = None,
    fun_fact: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Render form for creating or editing an offer.
    
    Args:
        offer: Existing offer for editing
        base_cost: Base cost for new offers
        route_description: Route description for new offers
        fun_fact: Fun fact for new offers
        
    Returns:
        Dictionary with form data if submitted, None otherwise
    """
    with st.form("offer_form"):
        # Status selection
        status = st.selectbox(
            "Status",
            options=[status.value for status in OfferStatus],
            index=0 if not offer else list(OfferStatus).index(offer.status),
            help="Current status of the offer"
        )
        
        # Pricing section
        st.markdown("### Pricing")
        col1, col2 = st.columns(2)
        
        with col1:
            margin_percentage = st.slider(
                "Margin Percentage",
                min_value=0,
                max_value=50,
                value=15 if not offer else float(offer.margin),
                help="Profit margin percentage to add to base cost"
            )
            
            if base_cost or (offer and offer.base_cost):
                current_base = base_cost or offer.base_cost
                margin_amount = current_base * (Decimal(margin_percentage) / 100)
                final_price = current_base + margin_amount
                
                st.metric("Base Cost", f"€{current_base:,.2f}")
                st.metric("Margin Amount", f"€{margin_amount:,.2f}")
                st.metric("Final Price", f"€{final_price:,.2f}")
        
        with col2:
            priority_pricing = st.radio(
                "Pricing Strategy",
                ["Standard", "Rush Hour", "Off-Peak"],
                help="Select pricing strategy based on delivery timing"
            )
            
            if priority_pricing == "Rush Hour":
                st.warning("Rush hour pricing adds 10% to the margin")
            elif priority_pricing == "Off-Peak":
                st.success("Off-peak pricing reduces margin by 5%")
        
        # Schedule section
        st.markdown("### Schedule")
        col1, col2 = st.columns(2)
        
        with col1:
            pickup_date = st.date_input(
                "Pickup Date",
                value=datetime.now().date() if not offer else offer.pickup_date.date(),
                min_value=datetime.now().date(),
                help="Select the earliest pickup date"
            )
            
            pickup_time = st.time_input(
                "Pickup Time",
                value=datetime.now().time() if not offer else offer.pickup_date.time(),
                help="Select preferred pickup time"
            )
        
        with col2:
            flexibility = st.selectbox(
                "Delivery Flexibility",
                ["Strict", "±1 day", "±2 days", "Flexible"],
                help="How flexible is the delivery timeline"
            )
            
            delivery_priority = st.radio(
                "Delivery Priority",
                ["Standard", "Express", "Premium"],
                help="Select the priority level for this transport"
            )
        
        # Additional services
        st.markdown("### Services & Requirements")
        col1, col2 = st.columns(2)
        
        with col1:
            additional_services = st.multiselect(
                "Additional Services",
                [
                    "Loading assistance",
                    "Unloading assistance",
                    "Real-time tracking",
                    "Insurance",
                    "Express delivery",
                    "Temperature monitoring",
                    "Security escort",
                    "Customs clearance"
                ],
                default=offer.additional_services if offer and offer.additional_services else [],
                help="Select any additional services needed"
            )
        
        with col2:
            special_requirements = st.text_area(
                "Special Requirements",
                value=offer.notes if offer and offer.notes else "",
                placeholder="Any special requirements or notes for the transport..."
            )
        
        # Version management
        if offer:
            st.markdown("### Version Management")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"Current Version: {offer.version}")
            
            with col2:
                change_reason = st.text_input(
                    "Change Reason",
                    placeholder="Reason for updating the offer...",
                    help="Required when modifying an existing offer"
                )
        
        # Fun fact
        include_fun_fact = st.checkbox(
            "Include Fun Fact",
            value=True if not offer else bool(offer.fun_fact),
            help="Add an AI-generated fun fact about the route"
        )
        
        # Submit button
        submit_label = "Update Offer" if offer else "Create Offer"
        submitted = st.form_submit_button(submit_label, type="primary")
        
        if submitted:
            # Validate form
            if offer and not change_reason:
                st.error("Please provide a reason for the change")
                return None
            
            # Calculate final price
            current_base = base_cost or (offer.base_cost if offer else Decimal("0"))
            margin_percentage = float(margin_percentage)
            
            if priority_pricing == "Rush Hour":
                margin_percentage += 10
            elif priority_pricing == "Off-Peak":
                margin_percentage = max(0, margin_percentage - 5)
            
            margin_amount = current_base * (Decimal(margin_percentage) / 100)
            final_price = current_base + margin_amount
            
            # Prepare metadata
            metadata = {
                "pricing_strategy": priority_pricing,
                "flexibility": flexibility,
                "delivery_priority": delivery_priority,
                "additional_services": additional_services,
                "special_requirements": special_requirements if special_requirements else None
            }
            
            if offer:
                metadata["change_reason"] = change_reason
                metadata["previous_version"] = offer.version
            
            # Return form data
            return {
                "id": str(UUID()) if not offer else offer.id,
                "status": status,
                "base_cost": float(current_base),
                "margin": margin_percentage,
                "final_price": float(final_price),
                "pickup_date": datetime.combine(pickup_date, pickup_time).replace(tzinfo=datetime.timezone.utc),
                "delivery_date": None,  # To be calculated based on route
                "fun_fact": fun_fact if include_fun_fact else None,
                "additional_services": additional_services,
                "notes": special_requirements if special_requirements else None,
                "metadata": metadata,
                "version": "1.0" if not offer else f"{float(offer.version) + 0.1:.1f}"
            }
        
        return None
