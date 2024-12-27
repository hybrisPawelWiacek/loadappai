"""
Offer management page.
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import streamlit as st
from streamlit import session_state as state

from src.domain.entities.offer import Offer, OfferHistory
from src.domain.entities.route import Route
from src.domain.services import OfferGenerationService
from src.frontend.components.offer_form import OfferForm
from src.frontend.components.offer_history import OfferHistoryView
from src.frontend.state.offer_state import OfferState
from src.infrastructure.logging import get_logger

def render_offer_list() -> None:
    """Render list of offers with filtering and pagination."""
    state, actions = use_offer_list()
    
    st.subheader("Manage Offers")
    
    # Filters
    with st.expander("Filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                options=[status.value for status in OfferStatus],
                help="Filter by offer status"
            )
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now().date(), datetime.now().date()),
                help="Filter by creation date"
            )
        
        with col3:
            price_range = st.slider(
                "Price Range (€)",
                min_value=0,
                max_value=10000,
                value=(0, 10000),
                step=100,
                help="Filter by price range"
            )
        
        # Apply filters button
        if st.button("Apply Filters"):
            filters = OfferFilters(
                status=status_filter if status_filter else None,
                created_after=datetime.combine(date_range[0], datetime.min.time()),
                created_before=datetime.combine(date_range[1], datetime.max.time()),
                min_price=float(price_range[0]),
                max_price=float(price_range[1])
            )
            actions['apply_filters'](filters)
    
    # Pagination
    total_pages = (state.total_offers + state.per_page - 1) // state.per_page
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if state.current_page > 1:
            if st.button("← Previous"):
                actions['load_page'](state.current_page - 1)
    
    with col2:
        st.write(f"Page {state.current_page} of {total_pages}")
    
    with col3:
        if state.current_page < total_pages:
            if st.button("Next →"):
                actions['load_page'](state.current_page + 1)
    
    # Loading state
    if state.is_loading:
        st.spinner("Loading offers...")
        return
    
    # Error state
    if state.error_message:
        st.error(state.error_message)
        if st.button("Retry"):
            actions['refresh']()
        return
    
    # Offer list
    for offer in state.offers:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**ID:** {offer.id}")
                st.write(f"**Status:** {offer.status}")
                st.write(f"**Version:** {offer.version}")
            
            with col2:
                st.metric(
                    "Price",
                    f"€{offer.final_price:,.2f}",
                    delta=f"Margin: {offer.margin:.1f}%"
                )
            
            with col3:
                if st.button("View Details", key=f"view_{offer.id}"):
                    st.session_state["selected_offer"] = offer.id
            
            st.markdown("---")


def render_offer_details(offer_id: str) -> None:
    """Render detailed view of an offer with version history."""
    state, actions = use_offer_details(offer_id)
    
    # Initial load
    if not state.selected_offer:
        actions['load']()
    
    st.subheader("Offer Details")
    
    # Loading state
    if state.is_loading:
        st.spinner("Loading offer details...")
        return
    
    # Error state
    if state.error_message:
        st.error(state.error_message)
        if st.button("Retry"):
            actions['load']()
        return
    
    # Success message
    if state.success_message:
        st.success(state.success_message)
    
    # Offer details
    offer = state.selected_offer
    if not offer:
        st.error("Offer not found")
        return
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Details", "History", "Compare Versions"])
    
    # Details tab
    with tab1:
        if state.is_editing:
            # Edit form
            form_state, form_actions = use_offer_form()
            form_data = render_offer_form(offer=offer)
            
            if form_data:
                form_actions['update_form']('form_data', form_data)
                if form_actions['validate']():
                    if form_actions['submit']():
                        form_actions['reset']()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel"):
                    actions['cancel_edit']()
        else:
            # Display mode
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Final Price",
                    f"€{offer.final_price:,.2f}",
                    delta=f"Margin: {offer.margin:.1f}%"
                )
            
            with col2:
                st.write(f"**Status:** {offer.status}")
                st.write(f"**Version:** {offer.version}")
            
            with col3:
                st.write(f"**Created:** {offer.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Modified:** {offer.modified_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Edit"):
                    actions['start_edit']()
            
            with col2:
                if offer.status != OfferStatus.ARCHIVED:
                    if st.button("Archive"):
                        if actions['archive']():
                            st.session_state["selected_offer"] = None
            
            with col3:
                if st.button("Back to List"):
                    st.session_state["selected_offer"] = None
    
    # History tab
    with tab2:
        history_state, history_actions = use_offer_history()
        
        display_version_history(
            state.history_entries,
            state.total_history,
            page=state.history_page
        )
    
    # Compare versions tab
    with tab3:
        history_state, history_actions = use_offer_history()
        
        selected_versions = render_version_selector(offer.id, state.history_entries)
        if selected_versions:
            version1, version2 = selected_versions
            history_actions['select_versions'](version1, version2)
            
            # Get version entries
            v1_entry = next((h for h in state.history_entries if h.version == version1), None)
            v2_entry = next((h for h in state.history_entries if h.version == version2), None)
            
            if v1_entry and v2_entry:
                compare_versions(v1_entry, v2_entry)


def render_page() -> None:
    """Render the offer management page."""
    st.title("Offer Management")
    
    # Create new offer button
    if st.button("Create New Offer", type="primary"):
        st.session_state["creating_offer"] = True
    
    # Handle different states
    if "creating_offer" in st.session_state and st.session_state["creating_offer"]:
        st.subheader("Create New Offer")
        state, actions = use_offer_form()
        
        form_data = render_offer_form()
        if form_data:
            actions['update_form']('form_data', form_data)
            if actions['validate']():
                if actions['submit']():
                    actions['reset']()
                    st.session_state["creating_offer"] = False
    
    elif "selected_offer" in st.session_state and st.session_state["selected_offer"]:
        render_offer_details(st.session_state["selected_offer"])
    
    else:
        render_offer_list()
