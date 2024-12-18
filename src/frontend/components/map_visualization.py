"""
Map visualization component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import folium
from streamlit_folium import st_folium

@dataclass
class RouteSegment:
    """Data class for route segments."""
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    distance_km: float
    duration_hours: float
    is_empty_driving: bool = False
    country: Optional[str] = None

def create_route_map(
    segments: List[RouteSegment],
    center: Optional[Tuple[float, float]] = None
) -> None:
    """Create and display an interactive map with route segments.
    
    Args:
        segments: List of route segments to display
        center: Optional center coordinates for the map
    """
    if not segments:
        st.warning("No route segments to display")
        return
    
    # Calculate map center if not provided
    if not center:
        all_lats = []
        all_lons = []
        for segment in segments:
            all_lats.extend([segment.start_location[0], segment.end_location[0]])
            all_lons.extend([segment.start_location[1], segment.end_location[1]])
        center = (sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons))
    
    # Create the map
    m = folium.Map(location=center, zoom_start=6)
    
    # Add route segments
    for segment in segments:
        # Different colors for loaded vs empty driving
        color = "red" if segment.is_empty_driving else "blue"
        
        # Create a line for the segment
        points = [segment.start_location, segment.end_location]
        folium.PolyLine(
            points,
            weight=3,
            color=color,
            opacity=0.8
        ).add_to(m)
        
        # Add markers for start and end points
        folium.Marker(
            segment.start_location,
            popup=f"Start: {segment.country if segment.country else 'Unknown'}"
        ).add_to(m)
        
        folium.Marker(
            segment.end_location,
            popup=f"End: {segment.country if segment.country else 'Unknown'}"
        ).add_to(m)
    
    # Display the map
    st_folium(m, width=800, height=400)

def display_route_timeline(segments: List[RouteSegment]) -> None:
    """Display a timeline of route events.
    
    Args:
        segments: List of route segments to display in timeline
    """
    st.subheader("Route Timeline")
    
    # Create timeline using Streamlit's native components
    for i, segment in enumerate(segments):
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.write(f"Segment {i+1}")
                if segment.is_empty_driving:
                    st.write("(Empty)")
            
            with col2:
                st.write(f"Distance: {segment.distance_km:.1f} km")
                st.write(f"Duration: {segment.duration_hours:.1f} hours")
                if segment.country:
                    st.write(f"Country: {segment.country}")
            
            with col3:
                if i == 0:
                    st.write("Start")
                elif i == len(segments) - 1:
                    st.write("End")
                else:
                    st.write("Transit")
            
            st.markdown("---")
