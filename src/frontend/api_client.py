"""API client for LoadApp.AI backend."""
import uuid
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from enum import Enum
from decimal import Decimal
import structlog
from http import HTTPStatus

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
        """Get route by ID.
        
        Args:
            route_id: Route ID
            
        Returns:
            Route data
        """
        return self._make_request('GET', f'/api/v1/routes/{route_id}')
        
    def get_route_cost(self, route_id: str) -> Dict:
        """Get cost calculation for a route.
        
        Args:
            route_id: Route ID
            
        Returns:
            Cost calculation data
        """
        return self._make_request('GET', f'/api/v1/routes/{route_id}/costs')
        
    def create_offer(self, offer_data: Dict) -> Dict:
        """Create a new offer.
        
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
