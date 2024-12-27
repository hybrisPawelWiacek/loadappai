"""API client for LoadApp.AI backend."""
import uuid
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from enum import Enum
from decimal import Decimal
import structlog
from http import HTTPStatus

from src.frontend.components.route_form import RouteFormData, Location
from src.frontend.components.map_visualization import RouteSegment, TimelineEventType
from src.frontend.components.cost_calculation import EnhancedCostBreakdown

# Configure logging
logger = structlog.get_logger(__name__)

class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class APIClient:
    """Client for LoadApp.AI backend API."""
    
    def __init__(self, base_url: str, api_key: str):
        """Initialize API client.
        
        Args:
            base_url: Base URL for API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.logger = logger.bind(component="api_client")
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Api-Key': api_key
        })
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIError: If the request fails
        """
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        url = f"{self.base_url}{endpoint}"
        
        # Add request ID to headers
        headers = {
            'X-Request-ID': request_id,
            **self.session.headers
        }
        
        # Add headers to kwargs
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers
            
        # Log request details
        self.logger.info(
            "api_request_started",
            request_id=request_id,
            method=method,
            url=url,
            headers={k: v for k, v in headers.items() if k not in ['X-Api-Key']},
            data=kwargs.get("json_data"),
            params=kwargs.get("params")
        )
        
        try:
            if "json_data" in kwargs:
                data = kwargs.pop("json_data")
                kwargs["json"] = data
                
            response = requests.request(method, url, **kwargs)
            
            # Log response details
            self.logger.info(
                "api_request_completed",
                request_id=request_id,
                status_code=response.status_code,
                url=url,
                response_text=response.text[:1000] if response.text else None
            )
            
            if response.status_code >= 400:
                self.logger.error(
                    "api_request_failed",
                    request_id=request_id,
                    status_code=response.status_code,
                    url=url,
                    response_text=response.text
                )
                raise APIError(f"API request failed: {response.text}")
                
            return response.json() if response.text else None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "api_request_error",
                request_id=request_id,
                error=str(e),
                url=url
            )
            raise APIError(f"API request failed: {str(e)}")
            
    def create_route(self, route_data: Dict) -> Dict:
        """Create a new route.
        
        Args:
            route_data: Route data
            
        Returns:
            Created route data
        """
        return self._make_request('POST', '/api/v1/routes', json_data=route_data)
        
    def get_route(self, route_id: str) -> Dict:
        """Get route details by ID.
        
        Args:
            route_id: ID of the route to fetch
            
        Returns:
            Route data containing:
                - id: str
                - origin: Dict[str, Any]
                - destination: Dict[str, Any]
                - distance_km: float
                - duration_hours: float
                - segments: List[Dict]
                - metadata: Dict
                - created_at: str
                - modified_at: str
        """
        return self._make_request('GET', f'/api/v1/routes/{route_id}')
        
    def get_route_cost(self, route_id: str) -> Dict:
        """Get cost calculation for a route.
        
        Args:
            route_id: Route ID
            
        Returns:
            Cost calculation data
        """
        return self._make_request('POST', f'/api/v1/routes/{route_id}/costs')
        
    def create_offer(self, offer_data: Dict) -> Dict:
        """Create a new offer with AI-enhanced content.
        
        Args:
            offer_data: Dictionary containing:
                - route_id: str
                - margin: float
                - transport_type: str
                - cargo_type: str
                - additional_services: List[str]
                - notes: Optional[str]
                - total_cost: Optional[float]
                
        Returns:
            Created offer data containing:
                - id: str
                - final_price: float
                - total_cost: float
                - margin: float
                - status: str
                - fun_fact: Optional[str]
                - description: Optional[str]
                - metadata: Dict
                - created_at: str
                - modified_at: str
        """
        try:
            # Get route data for AI content generation
            route_data = self.get_route(offer_data['route_id'])
            
            # Generate fun fact using OpenAI service
            fun_fact = self._make_request(
                'POST', 
                '/api/v1/ai/generate-fun-fact',
                json_data={'route': route_data}
            ).get('fun_fact')
            
            # Add fun fact to offer data
            if fun_fact:
                offer_data['fun_fact'] = fun_fact
                
            # Create the offer
            return self._make_request('POST', '/api/v1/offers', json_data=offer_data)
            
        except Exception as e:
            logger.error("Failed to create offer with AI content", error=str(e))
            # Fallback to creating offer without AI content
            return self._make_request('POST', '/api/v1/offers', json_data=offer_data)
        
    def get_offer(self, offer_id: str) -> Dict:
        """Get offer by ID.
        
        Args:
            offer_id: Offer ID
            
        Returns:
            Offer data
        """
        return self._make_request('GET', f'/api/v1/offers/{offer_id}')
        
    def update_offer(self, offer_id: str, offer_data: Dict) -> Dict:
        """Update an offer.
        
        Args:
            offer_id: Offer ID
            offer_data: Offer update data
            
        Returns:
            Updated offer data
        """
        return self._make_request('PUT', f'/api/v1/offers/{offer_id}', json_data=offer_data)
        
    def archive_offer(self, offer_id: str) -> Dict:
        """Archive an offer.
        
        Args:
            offer_id: Offer ID
            
        Returns:
            Updated offer data
        """
        return self._make_request('POST', f'/api/v1/offers/{offer_id}/archive')
        
    def list_routes(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict] = None
    ) -> Dict:
        """List routes with pagination and filtering.
        
        Args:
            page: Page number
            per_page: Items per page
            filters: Optional filters
            
        Returns:
            List of routes and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        if filters:
            params.update(filters)
        
        return self._make_request('GET', '/api/v1/routes', params=params)
    
    def update_route(self, route_id: str, route_data: Dict) -> Dict:
        """Update an existing route.
        
        Args:
            route_id: Route ID
            route_data: Route update data
            
        Returns:
            Updated route data
        """
        return self._make_request('PUT', f'/api/v1/routes/{route_id}', json_data=route_data)
    
    def delete_route(self, route_id: str) -> None:
        """Delete a route.
        
        Args:
            route_id: Route ID
        """
        self._make_request('DELETE', f'/api/v1/routes/{route_id}')

    def calculate_costs(
        self,
        route_id: str,
        calculation_options: Dict
    ) -> Dict:
        """Calculate costs for a route with detailed options.
        
        Args:
            route_id: Route ID
            calculation_options: Dictionary containing:
                - include_empty_driving: bool
                - include_country_breakdown: bool
                - include_time_costs: bool
                - include_cargo_costs: bool
                - include_overheads: bool
                - show_preliminary: bool
                - calculation_method: str
            
        Returns:
            Detailed cost breakdown
        """
        return self._make_request(
            'POST',
            f'/api/v1/routes/{route_id}/costs',
            json_data=calculation_options
        )
    
    def get_cost_settings(self) -> Dict:
        """Get current cost calculation settings.
        
        Returns:
            Dictionary containing:
                - base_rates: Dict[str, Dict[str, Decimal]]
                - time_based_rates: Dict[str, Decimal]
                - empty_driving_factors: Dict[str, float]
                - cargo_factors: Dict[str, float]
                - equipment_costs: Dict[str, Decimal]
                - margin_percentage: float
                - currency: str
                - version: str
        """
        return self._make_request('GET', '/api/settings/costs')
    
    def update_cost_settings(self, settings: Dict) -> Dict:
        """Update cost calculation settings.
        
        Args:
            settings: Dictionary containing:
                - base_rates: Dict[str, Dict[str, Decimal]]
                - time_based_rates: Dict[str, Decimal]
                - empty_driving_factors: Dict[str, float]
                - cargo_factors: Dict[str, float]
                - equipment_costs: Dict[str, Decimal]
                - margin_percentage: float
                - currency: str
                
        Returns:
            Updated settings
        """
        return self._make_request(
            'PUT',
            '/api/settings/costs',
            json_data=settings
        )
    
    def get_transport_settings(self) -> Dict:
        """Get current transport settings.
        
        Returns:
            Dictionary containing vehicle and cargo configurations
        """
        return self._make_request('GET', '/api/settings/transport')
    
    def update_transport_settings(self, settings: Dict) -> Dict:
        """Update transport settings.
        
        Args:
            settings: Dictionary containing:
                - vehicle_types: List[Dict] with specifications
                - cargo_types: List[str]
                
        Returns:
            Updated settings
        """
        return self._make_request(
            'PUT',
            '/api/settings/transport',
            json_data=settings
        )

    def get_system_settings(self) -> Dict:
        """Get current system settings.
        
        Returns:
            Dictionary containing system configuration
        """
        return self._make_request('GET', '/api/settings/system')
    
    def update_system_settings(self, settings: Dict) -> Dict:
        """Update system settings.
        
        Args:
            settings: Dictionary containing:
                - calculation_method: str
                - show_preliminary: bool
                - cache_duration: int
                - enable_auto_refresh: bool
                - api_url: str
                - enable_cache: bool
                
        Returns:
            Updated settings
        """
        return self._make_request(
            'PUT',
            '/api/settings/system',
            json_data=settings
        )

    def get_cost_history(
        self,
        route_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        version: Optional[str] = None
    ) -> List[Dict]:
        """Get cost calculation history for a route.
        
        Args:
            route_id: Route ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            version: Optional version filter
            
        Returns:
            List of historical cost calculations
        """
        params = {}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if version:
            params['version'] = version
        
        return self._make_request(
            'GET',
            f'/api/v1/routes/{route_id}/costs/history',
            params=params
        )
    
    def validate_cost_settings(self, settings: Dict) -> Dict:
        """Validate cost settings before applying them.
        
        Args:
            settings: Cost settings to validate
            
        Returns:
            Validation results with any warnings or suggestions
        """
        return self._make_request(
            'POST',
            '/api/settings/costs/validate',
            json_data=settings
        )

    def get_route_cost(self, route_id: str) -> Optional[EnhancedCostBreakdown]:
        """Get cost calculation for a route.
        
        Args:
            route_id: Route ID
            
        Returns:
            Cost calculation data as EnhancedCostBreakdown object, or None if calculation fails
        """
        try:
            cost_data = self._make_request('POST', f'/api/v1/routes/{route_id}/costs')
            if not cost_data:
                self.logger.warning("No cost data received from API", route_id=route_id)
                return None
                
            # Convert all numeric values to Decimal
            for country, costs in cost_data.get('fuel_costs', {}).items():
                cost_data['fuel_costs'][country] = Decimal(str(costs))
            for country, costs in cost_data.get('toll_costs', {}).items():
                cost_data['toll_costs'][country] = Decimal(str(costs))
            for country, costs in cost_data.get('driver_costs', {}).items():
                cost_data['driver_costs'][country] = Decimal(str(costs))
                
            cost_data['rest_period_costs'] = Decimal(str(cost_data.get('rest_period_costs', 0)))
            cost_data['loading_unloading_costs'] = Decimal(str(cost_data.get('loading_unloading_costs', 0)))
            
            # Convert empty driving costs
            empty_driving_costs = {}
            for country, costs in cost_data.get('empty_driving_costs', {}).items():
                empty_driving_costs[country] = {
                    k: Decimal(str(v)) for k, v in costs.items()
                }
            cost_data['empty_driving_costs'] = empty_driving_costs
            
            # Convert cargo specific costs
            cost_data['cargo_specific_costs'] = {
                k: Decimal(str(v)) for k, v in cost_data.get('cargo_specific_costs', {}).items()
            }
            
            # Convert overhead costs
            cost_data['overheads'] = {
                k: Decimal(str(v)) for k, v in cost_data.get('overheads', {}).items()
            }
            
            return EnhancedCostBreakdown(**cost_data)
            
        except Exception as e:
            self.logger.error("Error getting route cost", route_id=route_id, error=str(e))
            return None

    def submit_route(self, form_data: 'RouteFormData') -> Tuple[List['RouteSegment'], datetime, str]:
        """Submit route data to backend API and convert response to frontend models.
        
        Args:
            form_data: Route form data containing origin, destination, and transport details
            
        Returns:
            Tuple containing:
                - List of route segments
                - Pickup time
                - Route ID
                
        Raises:
            APIError: If the request fails
        """
        # Prepare request data with cargo specs from form data
        cargo_specs = {
            "weight_kg": form_data.cargo_specs.weight_kg if form_data.cargo_specs else 0,
            "volume_m3": form_data.cargo_specs.volume_m3 if form_data.cargo_specs else 0,
            "cargo_type": form_data.cargo_specs.cargo_type if form_data.cargo_specs else "General",
            "temperature_controlled": form_data.cargo_specs.temperature_controlled if form_data.cargo_specs else False,
            "required_temp_celsius": form_data.cargo_specs.required_temp_celsius if form_data.cargo_specs else None,
            "hazmat_class": form_data.cargo_specs.hazmat_class if form_data.cargo_specs else None
        }
        
        request_data = {
            "origin": {
                "address": form_data.origin.address,
                "latitude": form_data.origin.latitude,
                "longitude": form_data.origin.longitude,
                "country": form_data.origin.country
            },
            "destination": {
                "address": form_data.destination.address,
                "latitude": form_data.destination.latitude,
                "longitude": form_data.destination.longitude,
                "country": form_data.destination.country
            },
            "transport_type": form_data.transport_type,
            "pickup_time": form_data.pickup_time.isoformat(),
            "delivery_time": form_data.delivery_time.isoformat(),
            "cargo_specs": cargo_specs
        }

        # Send request to backend
        route_data = self._make_request('POST', '/api/v1/routes', json_data=request_data)
        route_id = route_data.get("id")
        segments = []
        
        # Create timeline segments
        # 1. Loading at origin
        loading_segment = RouteSegment(
            start_location=Location(
                address=route_data["origin"]["address"],
                latitude=route_data["origin"]["latitude"],
                longitude=route_data["origin"]["longitude"],
                country=route_data["origin"]["country"]
            ),
            end_location=Location(
                address=route_data["origin"]["address"],
                latitude=route_data["origin"]["latitude"],
                longitude=route_data["origin"]["longitude"],
                country=route_data["origin"]["country"]
            ),
            distance_km=0,
            duration_hours=0.5,  # 30 minutes for loading
            country=route_data["origin"]["country"],
            is_empty_driving=False,
            timeline_event=TimelineEventType.PICKUP
        )
        segments.append(loading_segment)
        
        # 2. Main transport segment
        main_segment = RouteSegment(
            start_location=Location(
                address=route_data["origin"]["address"],
                latitude=route_data["origin"]["latitude"],
                longitude=route_data["origin"]["longitude"],
                country=route_data["origin"]["country"]
            ),
            end_location=Location(
                address=route_data["destination"]["address"],
                latitude=route_data["destination"]["latitude"],
                longitude=route_data["destination"]["longitude"],
                country=route_data["destination"]["country"]
            ),
            distance_km=route_data["distance_km"],
            duration_hours=route_data["duration_hours"],
            country=route_data["origin"]["country"],
            is_empty_driving=False,
            timeline_event=TimelineEventType.LOADED_DRIVING
        )
        segments.append(main_segment)
        
        # 3. Unloading at destination
        unloading_segment = RouteSegment(
            start_location=Location(
                address=route_data["destination"]["address"],
                latitude=route_data["destination"]["latitude"],
                longitude=route_data["destination"]["longitude"],
                country=route_data["destination"]["country"]
            ),
            end_location=Location(
                address=route_data["destination"]["address"],
                latitude=route_data["destination"]["latitude"],
                longitude=route_data["destination"]["longitude"],
                country=route_data["destination"]["country"]
            ),
            distance_km=0,
            duration_hours=0.5,  # 30 minutes for unloading
            country=route_data["destination"]["country"],
            is_empty_driving=False,
            timeline_event=TimelineEventType.DELIVERY
        )
        segments.append(unloading_segment)
        
        # Add empty driving segment if present
        if route_data.get("empty_driving") and route_data["empty_driving"].get("start_location"):
            empty = route_data["empty_driving"]
            empty_segment = RouteSegment(
                start_location=Location(
                    address=empty["start_location"]["address"],
                    latitude=empty["start_location"]["latitude"],
                    longitude=empty["start_location"]["longitude"],
                    country=empty["start_location"]["country"]
                ),
                end_location=Location(
                    address=empty["end_location"]["address"],
                    latitude=empty["end_location"]["latitude"],
                    longitude=empty["end_location"]["longitude"],
                    country=empty["end_location"]["country"]
                ),
                distance_km=empty["distance_km"],
                duration_hours=empty["duration_hours"],
                country=empty["start_location"]["country"],
                is_empty_driving=True,
                timeline_event=TimelineEventType.EMPTY_DRIVING
            )
            segments.append(empty_segment)
        
        return segments, form_data.pickup_time, route_id
