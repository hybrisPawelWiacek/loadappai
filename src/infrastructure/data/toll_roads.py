"""Toll road data for various countries."""
from typing import Dict, Set

# Known toll roads and motorways by country
TOLL_ROADS: Dict[str, Set[str]] = {
    "DE": {  # Germany
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
        "A11", "A12", "A13", "A14", "A15", "A19", "A20", "A24", "A25",
        "A26", "A27", "A28", "A29", "A30", "A31", "A33", "A37", "A38",
        "A39", "A40", "A42", "A43", "A44", "A45", "A46", "A48", "A49",
        "A52", "A57", "A59", "A60", "A61", "A62", "A63", "A64", "A65",
        "A66", "A67", "A70", "A71", "A72", "A73", "A81", "A92", "A93",
        "A94", "A95", "A96", "A98", "A99"
    },
    "FR": {  # France
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
        "A11", "A13", "A14", "A16", "A19", "A20", "A26", "A29", "A31",
        "A35", "A36", "A40", "A41", "A42", "A43", "A46", "A48", "A49",
        "A51", "A52", "A54", "A61", "A62", "A63", "A64", "A71", "A75",
        "A77", "A81", "A83", "A85", "A87", "A89"
    },
    "PL": {  # Poland
        "A1", "A2", "A4",  # Main motorways
        "S1", "S3", "S5", "S7", "S8", "S17", "S19", "S61"  # Express roads
    },
    "CZ": {  # Czech Republic
        "D1", "D2", "D3", "D5", "D8", "D11"  # Main motorways
    },
    "AT": {  # Austria
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
        "A11", "A12", "A13", "A14", "A21", "A22", "A23", "A25"
    }
}

# Keywords that indicate toll roads in route descriptions
TOLL_KEYWORDS = {
    "toll", "maut", "péage", "autostrada", "dálnice",  # Various languages
    "motorway", "autobahn", "highway", "autoroute",
    "toll road", "toll highway", "toll motorway",
    "vignette", "toll charge", "toll fee"
}

# Base toll rates per kilometer by country and vehicle type
TOLL_RATES: Dict[str, Dict[str, float]] = {
    "DE": {  # Germany
        "truck": 0.20,
        "van": 0.15,
        "trailer": 0.25,
        "default": 0.15
    },
    "FR": {  # France - generally higher rates
        "truck": 0.25,
        "van": 0.18,
        "trailer": 0.30,
        "default": 0.18
    },
    "PL": {  # Poland - lower rates
        "truck": 0.15,
        "van": 0.10,
        "trailer": 0.20,
        "default": 0.10
    },
    "CZ": {  # Czech Republic
        "truck": 0.18,
        "van": 0.12,
        "trailer": 0.22,
        "default": 0.12
    },
    "AT": {  # Austria
        "truck": 0.22,
        "van": 0.16,
        "trailer": 0.28,
        "default": 0.16
    },
    "default": {  # Default rates if country not found
        "truck": 0.20,
        "van": 0.15,
        "trailer": 0.25,
        "default": 0.15
    }
}

def is_toll_road(road_name: str, country_code: str) -> bool:
    """Check if a road is a toll road.
    
    Args:
        road_name: Name of the road (e.g., "A1", "E40")
        country_code: ISO country code
        
    Returns:
        True if road is a toll road
    """
    # Normalize road name (remove spaces, convert to uppercase)
    road_name = road_name.upper().replace(" ", "")
    
    # Check if road is in country's toll road list
    country_roads = TOLL_ROADS.get(country_code, set())
    return road_name in country_roads

def get_toll_rate(country_code: str, vehicle_type: str) -> float:
    """Get toll rate for a country and vehicle type.
    
    Args:
        country_code: ISO country code
        vehicle_type: Type of vehicle (truck, van, trailer)
        
    Returns:
        Toll rate per kilometer
    """
    # Get country rates or default rates
    country_rates = TOLL_RATES.get(country_code, TOLL_RATES["default"])
    # Get vehicle rate or default rate for country
    return country_rates.get(vehicle_type.lower(), country_rates["default"])
