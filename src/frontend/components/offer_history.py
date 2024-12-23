"""
Offer history and version management component for LoadApp.AI
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import streamlit as st

from src.domain.entities import OfferHistory as OfferHistoryEntity


def display_version_history(
    history_entries: List[OfferHistoryEntity],
    total_entries: int,
    page: int = 1,
    per_page: int = 10
) -> None:
    """
    Display version history of an offer with pagination.
    
    Args:
        history_entries: List of history entries
        total_entries: Total number of history entries
        page: Current page number (1-based)
        per_page: Number of entries per page
    """
    st.subheader("Version History")
    
    # Display pagination controls
    total_pages = (total_entries + per_page - 1) // per_page
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if page > 1:
            if st.button("← Previous"):
                st.session_state["history_page"] = page - 1
    
    with col2:
        st.write(f"Page {page} of {total_pages}")
    
    with col3:
        if page < total_pages:
            if st.button("Next →"):
                st.session_state["history_page"] = page + 1
    
    # Display history entries
    for entry in history_entries:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Version {entry.version}**")
                st.write(f"Changed by: {entry.changed_by}")
                st.write(f"Reason: {entry.change_reason}")
            
            with col2:
                st.write(f"Status: {entry.status}")
                st.write(f"Changed at: {entry.changed_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Show changes
            with st.expander("View Changes"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Price",
                        f"€{entry.final_price:,.2f}",
                        delta=f"Margin: {entry.margin:.1f}%"
                    )
                
                with col2:
                    if entry.fun_fact:
                        st.info(f"**Fun Fact:** {entry.fun_fact}")
                
                if entry.metadata:
                    st.json(entry.metadata)
            
            st.markdown("---")


def compare_versions(
    version1: OfferHistoryEntity,
    version2: OfferHistoryEntity
) -> None:
    """
    Compare two versions of an offer side by side.
    
    Args:
        version1: First version to compare
        version2: Second version to compare
    """
    st.subheader("Version Comparison")
    
    col1, col2 = st.columns(2)
    
    # Helper function to display version details
    def display_version(version: OfferHistoryEntity, column):
        with column:
            st.markdown(f"**Version {version.version}**")
            st.write(f"Status: {version.status}")
            st.write(f"Changed by: {version.changed_by}")
            st.write(f"At: {version.changed_at.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"Reason: {version.change_reason}")
            
            st.markdown("#### Price Details")
            st.metric(
                "Final Price",
                f"€{version.final_price:,.2f}",
                delta=f"Margin: {version.margin:.1f}%"
            )
            
            if version.fun_fact:
                st.markdown("#### Fun Fact")
                st.info(version.fun_fact)
            
            if version.metadata:
                st.markdown("#### Metadata")
                st.json(version.metadata)
    
    # Display versions side by side
    display_version(version1, col1)
    display_version(version2, col2)
    
    # Highlight differences
    st.markdown("### Changes")
    changes = []
    
    if version1.status != version2.status:
        changes.append(f"Status changed from '{version1.status}' to '{version2.status}'")
    
    if version1.margin != version2.margin:
        changes.append(f"Margin changed from {version1.margin:.1f}% to {version2.margin:.1f}%")
    
    if version1.final_price != version2.final_price:
        diff = version2.final_price - version1.final_price
        changes.append(f"Price changed by €{abs(diff):,.2f} ({'increased' if diff > 0 else 'decreased'})")
    
    if version1.fun_fact != version2.fun_fact:
        changes.append("Fun fact was updated")
    
    if version1.metadata != version2.metadata:
        changes.append("Metadata was modified")
    
    if changes:
        for change in changes:
            st.write(f"- {change}")
    else:
        st.info("No significant changes found between these versions")


def render_version_selector(
    offer_id: str,
    history_entries: List[OfferHistoryEntity]
) -> Optional[Tuple[str, str]]:
    """
    Render version selection controls for comparison.
    
    Args:
        offer_id: ID of the offer
        history_entries: List of available versions
        
    Returns:
        Tuple of selected version numbers if comparison requested,
        None otherwise
    """
    st.subheader("Compare Versions")
    
    # Create version options
    versions = [(entry.version, f"Version {entry.version} ({entry.changed_at.strftime('%Y-%m-%d %H:%M')})") 
               for entry in history_entries]
    
    col1, col2 = st.columns(2)
    
    with col1:
        version1 = st.selectbox(
            "First Version",
            options=[v[0] for v in versions],
            format_func=lambda x: next(v[1] for v in versions if v[0] == x),
            key=f"v1_{offer_id}"
        )
    
    with col2:
        # Filter out the first selected version
        remaining_versions = [v for v in versions if v[0] != version1]
        version2 = st.selectbox(
            "Second Version",
            options=[v[0] for v in remaining_versions],
            format_func=lambda x: next(v[1] for v in remaining_versions if v[0] == x),
            key=f"v2_{offer_id}"
        )
    
    if st.button("Compare Versions"):
        return version1, version2
    
    return None
