"""
Offer generation component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

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
    with st.container():
        # Header with key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Final Price",
                f"€{offer.price:,.2f}",
                delta=f"Margin: {offer.margin_percentage:.1f}%"
            )
        
        with col2:
            st.metric(
                "Pickup",
                offer.pickup_date.strftime("%Y-%m-%d %H:%M")
            )
        
        with col3:
            st.metric(
                "Delivery",
                offer.delivery_date.strftime("%Y-%m-%d %H:%M")
            )
        
        # Detailed sections
        with st.expander("Transport Details", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Transport Type:**", offer.transport_type)
                st.write("**Base Cost:**", f"€{offer.base_cost:,.2f}")
            
            with col2:
                st.write("**Cargo Type:**", offer.cargo_type)
                st.write("**Margin Amount:**", f"€{offer.margin_amount:,.2f}")
        
        # Route description
        with st.expander("Route Description", expanded=True):
            st.write(offer.route_description)
            
            if offer.fun_fact:
                st.info(f"**Did you know?** {offer.fun_fact}")
        
        # Additional services if any
        if offer.additional_services:
            with st.expander("Additional Services"):
                for service in offer.additional_services:
                    st.write(f"- {service}")
        
        # Notes if any
        if offer.notes:
            with st.expander("Notes"):
                st.write(offer.notes)
        
        st.markdown("---")

def render_offer_controls(base_cost: Optional[Decimal] = None):
    """Render offer generation controls and settings.
    
    Args:
        base_cost: Optional base cost to calculate margins
    """
    st.subheader("Offer Settings")
    
    with st.form("offer_settings"):
        # Pricing section
        st.markdown("#### Pricing")
        col1, col2 = st.columns(2)
        
        with col1:
            margin_percentage = st.slider(
                "Margin Percentage",
                min_value=0,
                max_value=50,
                value=15,
                help="Profit margin percentage to add to base cost"
            )
            
            if base_cost:
                margin_amount = base_cost * (Decimal(margin_percentage) / 100)
                final_price = base_cost + margin_amount
                
                st.metric("Base Cost", f"€{base_cost:,.2f}")
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
        
        # Timing section
        st.markdown("#### Schedule")
        col1, col2 = st.columns(2)
        
        with col1:
            pickup_date = st.date_input(
                "Pickup Date",
                min_value=datetime.now().date(),
                help="Select the earliest pickup date"
            )
            
            pickup_time = st.time_input(
                "Pickup Time",
                value=datetime.now().time(),
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
        st.markdown("#### Services & Requirements")
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
                help="Select any additional services needed"
            )
        
        with col2:
            special_requirements = st.text_area(
                "Special Requirements",
                placeholder="Any special requirements or notes for the transport..."
            )
        
        # Fun fact generation
        include_fun_fact = st.checkbox(
            "Include Fun Fact",
            value=True,
            help="Add an AI-generated fun fact about the route to make the offer more engaging"
        )
        
        submitted = st.form_submit_button("Generate Offer")
        
        if submitted:
            return {
                "pricing": {
                    "margin_percentage": margin_percentage,
                    "strategy": priority_pricing
                },
                "schedule": {
                    "pickup_datetime": datetime.combine(pickup_date, pickup_time),
                    "flexibility": flexibility,
                    "priority": delivery_priority
                },
                "services": {
                    "additional": additional_services,
                    "requirements": special_requirements if special_requirements else None
                },
                "fun_fact": include_fun_fact
            }
        
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
    st.subheader("Offer Preview")
    
    # Calculate pricing
    margin_percentage = offer_settings["pricing"]["margin_percentage"]
    if offer_settings["pricing"]["strategy"] == "Rush Hour":
        margin_percentage += 10
    elif offer_settings["pricing"]["strategy"] == "Off-Peak":
        margin_percentage = max(0, margin_percentage - 5)
    
    margin_amount = base_cost * (Decimal(margin_percentage) / 100)
    final_price = base_cost + margin_amount
    
    # Display preview
    with st.container():
        st.markdown("### Transport Offer")
        
        # Pricing
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Price", f"€{final_price:,.2f}")
        with col2:
            st.metric("Base Cost", f"€{base_cost:,.2f}")
        with col3:
            st.metric("Margin", f"{margin_percentage}%")
        
        # Schedule
        st.markdown("#### Schedule")
        pickup = offer_settings["schedule"]["pickup_datetime"]
        st.write(f"**Pickup:** {pickup.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Flexibility:** {offer_settings['schedule']['flexibility']}")
        st.write(f"**Priority:** {offer_settings['schedule']['priority']}")
        
        # Route
        st.markdown("#### Route Details")
        st.write(route_description)
        
        if fun_fact and offer_settings["fun_fact"]:
            st.info(f"**Did you know?** {fun_fact}")
        
        # Services
        if offer_settings["services"]["additional"]:
            st.markdown("#### Additional Services")
            for service in offer_settings["services"]["additional"]:
                st.write(f"- {service}")
        
        if offer_settings["services"]["requirements"]:
            st.markdown("#### Special Requirements")
            st.write(offer_settings["services"]["requirements"])
        
        # Actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Offer", type="secondary"):
                st.session_state["editing_offer"] = True
        with col2:
            if st.button("Finalize Offer", type="primary"):
                st.session_state["offer_finalized"] = True
