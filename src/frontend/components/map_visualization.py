"""
Map visualization component for LoadApp.AI
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import folium
from folium import plugins
import requests
from streamlit_folium import st_folium
from datetime import datetime, timedelta
from src.config import get_settings

settings = get_settings()
GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY

class TimelineEventType(str, Enum):
    """Types of timeline events matching API specification."""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    EMPTY_DRIVING = "empty_driving"
    LOADED_DRIVING = "loaded_driving"

@dataclass
class Location:
    """Location data matching API specification."""
    address: str
    latitude: float
    longitude: float
    country: str

    def to_tuple(self) -> Tuple[float, float]:
        """Convert location to coordinate tuple."""
        return (self.latitude, self.longitude)

@dataclass
class RouteSegment:
    """Data class for route segments matching API specification."""
    start_location: Location
    end_location: Location
    distance_km: float
    duration_hours: float
    country: str
    is_empty_driving: bool = False
    timeline_event: Optional[TimelineEventType] = None

def get_segment_color(segment: RouteSegment) -> str:
    """Get color for route segment based on its type."""
    if segment.is_empty_driving:
        return "#808080"  # Gray for empty driving
    return "#2962FF"  # Blue for loaded driving

def get_segment_icon(segment: RouteSegment) -> str:
    """Get icon for route segment based on its type."""
    if segment.timeline_event == TimelineEventType.PICKUP:
        return "upload"  # Loading icon
    elif segment.timeline_event == TimelineEventType.DELIVERY:
        return "download"  # Unloading icon
    elif segment.timeline_event == TimelineEventType.EMPTY_DRIVING:
        return "truck"  # Empty truck icon
    elif segment.timeline_event == TimelineEventType.LOADED_DRIVING:
        return "truck"  # Loaded truck icon
    else:
        return "record"  # Default icon

def get_osrm_route(start_location: Location, end_location: Location) -> List[List[float]]:
    """Get driving route coordinates from OSRM."""
    try:
        # Use OSRM demo server - for production, you should use your own OSRM instance
        url = f"http://router.project-osrm.org/route/v1/driving/{start_location.longitude},{start_location.latitude};{end_location.longitude},{end_location.latitude}?overview=full&geometries=geojson"
        response = requests.get(url)
        route_data = response.json()
        
        if response.status_code == 200 and route_data.get("routes"):
            return route_data["routes"][0]["geometry"]["coordinates"]
        else:
            print(f"OSRM error: {route_data}")
            return None
    except Exception as e:
        print(f"Error getting OSRM route: {str(e)}")
        return None

def create_route_map(segments: List[RouteSegment], key: str) -> None:
    """Create and display an interactive map with route segments."""
    if not segments:
        st.warning("No route segments to display")
        return
    
    try:
        # Calculate map center and bounds
        all_lats = []
        all_lons = []
        for segment in segments:
            all_lats.extend([segment.start_location.latitude, segment.end_location.latitude])
            all_lons.extend([segment.start_location.longitude, segment.end_location.longitude])
        
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        
        # Create map with Google Maps tiles
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles=f'https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}',
            attr='Google Maps'
        )
        
        # Add additional Google Maps layers
        folium.TileLayer(
            f'https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}',
            name='Google Satellite',
            attr='Google Maps'
        ).add_to(m)
        
        folium.TileLayer(
            f'https://mt1.google.com/vt/lyrs=p&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}',
            name='Google Terrain',
            attr='Google Maps'
        ).add_to(m)
        
        # Add route segments with different colors
        for segment in segments:
            # Get actual driving route from OSRM
            route_coords = get_osrm_route(segment.start_location, segment.end_location)
            
            if route_coords:
                # Convert OSRM coordinates (lon, lat) to folium format (lat, lon)
                route_points = [[lat, lon] for lon, lat in route_coords]
                
                color = get_segment_color(segment)
                route_line = folium.PolyLine(
                    route_points,
                    color=color,
                    weight=4,
                    opacity=0.8,
                    popup=f"""
                    <div style='font-family: Arial, sans-serif;'>
                        <b>Route Segment</b><br>
                        Distance: {segment.distance_km:.1f} km<br>
                        Duration: {segment.duration_hours:.1f} hours<br>
                        Type: {'Empty driving' if segment.is_empty_driving else 'Loaded driving'}
                    </div>
                    """
                )
                route_line.add_to(m)
            
            # Add markers for start and end points
            folium.Marker(
                [segment.start_location.latitude, segment.start_location.longitude],
                popup=f"""
                <div style='font-family: Arial, sans-serif;'>
                    <b>{segment.start_location.address}</b><br>
                    Country: {segment.start_location.country}
                </div>
                """,
                icon=folium.Icon(
                    color="green" if not segment.is_empty_driving else "gray",
                    icon=get_segment_icon(segment)
                )
            ).add_to(m)
        
        # Add final destination marker
        last_segment = segments[-1]
        folium.Marker(
            [last_segment.end_location.latitude, last_segment.end_location.longitude],
            popup=f"""
            <div style='font-family: Arial, sans-serif;'>
                <b>{last_segment.end_location.address}</b><br>
                Country: {last_segment.end_location.country}
            </div>
            """,
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        
        # Add layer control and fullscreen option
        folium.LayerControl().add_to(m)
        plugins.Fullscreen().add_to(m)
        
        # Fit map bounds to show all markers
        bounds = [[min(all_lats), min(all_lons)], [max(all_lats), max(all_lons)]]
        m.fit_bounds(bounds)
        
        # Display the map with increased height for better visibility
        st_folium(m, key=key, width=800, height=600)
        
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        import traceback
        print(f"Map creation error: {str(e)}")
        print(traceback.format_exc())

def display_route_timeline(segments: List[RouteSegment], pickup_time: datetime) -> None:
    """Display a timeline of route events."""
    if not segments:
        st.warning("No route segments to display in timeline")
        return
    
    # Calculate cumulative time for each segment
    current_time = pickup_time
    
    # Create timeline using Streamlit's native components
    for i, segment in enumerate(segments):
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                time_str = current_time.strftime("%H:%M")
                st.write(f"**{time_str}**")
                if segment.timeline_event:
                    st.write(f"*{segment.timeline_event.value}*")
            
            with col2:
                st.write(f"**{segment.start_location.address}** →")
                st.write(f"**{segment.end_location.address}**")
                st.write(f"Country: {segment.country}")
            
            with col3:
                st.write(f"Distance: {segment.distance_km:.1f} km")
                st.write(f"Duration: {segment.duration_hours:.1f} hours")
                if segment.is_empty_driving:
                    st.write(" Empty driving")
                elif segment.timeline_event == TimelineEventType.PICKUP:
                    st.write(" Loading")
                elif segment.timeline_event == TimelineEventType.DELIVERY:
                    st.write(" Delivery")
                elif segment.timeline_event == TimelineEventType.LOADED_DRIVING:
                    st.write(" Loaded driving")
            
            current_time = current_time + timedelta(hours=segment.duration_hours)
            
            # Add a divider between segments
            if i < len(segments) - 1:
                st.divider()
