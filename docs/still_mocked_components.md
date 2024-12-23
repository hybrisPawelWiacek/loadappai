# Still Mocked Components in LoadApp.AI

This document outlines components that are currently mocked or have hard-coded assumptions in the cost calculation logic. These items should be considered for future implementation or integration with real data sources.

## Cost Settings and Rates

### Fuel Prices
- Default fuel prices are hard-coded for each country
- No integration with real-time fuel price APIs
- No historical price tracking
- No differentiation between diesel and other fuel types
- Missing seasonal price variations

### Toll Rates
- Fixed highway/national road split (70/30)
- Static toll rates per country
- No integration with real toll calculation APIs
- Missing:
  - Time-based variations (peak/off-peak)
  - Vehicle class differentiation
  - Special zones or congestion charges
  - Electronic toll collection discounts

### Driver Rates
- Static hourly rates per country
- Missing:
  - Experience-based rate variations
  - Overtime calculations
  - Night/weekend differentials
  - Holiday pay rates
  - Per diem allowances

## Route Calculations

### Empty Driving
- Simplified empty driving factors:
  - Fixed 80% fuel consumption
  - Fixed toll rates (100%)
  - Fixed driver rates (100%)
- No optimization for:
  - Return load opportunities
  - Multi-stop route optimization
  - Backhaul planning

### Distance Calculations
- Highway vs. national road split is fixed
- No consideration of:
  - Real-time traffic conditions
  - Road works or closures
  - Seasonal route variations
  - Low emission zones
  - Vehicle height/weight restrictions

### Route Segmentation
- Fixed country segment split (60/40 for Poland/Germany)
- Hard-coded total distance (571.725 km)
- Hard-coded total duration (5.89 hours)
- No actual route waypoint analysis
- Missing:
  - Border crossing points
  - Actual country transition points
  - Segment-specific route characteristics

### API Integration Limitations
- Limited use of Google Maps API features:
  - No waypoint optimization
  - No traffic prediction integration
  - No route alternatives analysis
  - No consideration of truck-specific routes
  - Missing height/weight restriction checks

### Country Code Mapping
- Static country code mapping
- Limited to specific European countries
- No dynamic country resolution
- Missing:
  - Region-specific regulations
  - Cross-border documentation requirements
  - International transport permits

### Vehicle Routing Constraints
- No consideration of:
  - Vehicle dimensions
  - Weight limits
  - Hazardous material restrictions
  - Time-based access restrictions
  - Environmental zones
  - Bridge/tunnel restrictions

### Route Optimization
- Missing:
  - Alternative route comparison
  - Cost-based route optimization
  - Time-based route optimization
  - Multi-stop optimization
  - Break point optimization
  - Fuel stop planning

## Time-Based Calculations

### Rest Periods
- Simplified rest period calculations
- Missing:
  - Complex driving time regulations
  - Weekly rest requirements
  - Reduced/extended rest periods
  - Multiple driver scenarios

### Loading/Unloading
- Fixed loading/unloading rates
- No consideration of:
  - Facility-specific waiting times
  - Equipment requirements
  - Special handling needs
  - Loading dock availability
  - Appointment windows

## Vehicle-Specific Factors

### Maintenance Costs
- Fixed maintenance rate per km
- Missing:
  - Vehicle age consideration
  - Terrain impact
  - Seasonal variations
  - Preventive maintenance schedules
  - Tire wear calculations

### Fuel Consumption
- Fixed fuel consumption rates
- No consideration of:
  - Vehicle specifications
  - Load weight impact
  - Weather conditions
  - Driving style
  - Terrain effects

## Cargo-Specific Calculations

### Special Requirements
- Basic cargo type differentiation
- Missing:
  - Detailed handling requirements
  - Special equipment needs
  - Insurance requirements
  - Documentation costs
  - Customs procedures

### Temperature Control
- Basic temperature control flag
- Missing:
  - Energy consumption calculations
  - Temperature monitoring costs
  - Backup systems requirements
  - Pre-cooling costs

## Business Overheads

### Fixed Costs
- Simplified overhead structure
- Missing:
  - Insurance costs
  - Administrative expenses
  - Fleet management costs
  - Training expenses
  - Compliance costs

### Variable Costs
- Basic distance and time-based rates
- Missing:
  - Seasonal variations
  - Market condition adjustments
  - Volume-based discounts
  - Long-term contract rates

## Future Integration Points

### Real-Time Data Sources
1. Fuel Price APIs
   - Market price feeds
   - Local station networks
   - Bulk purchase agreements

2. Traffic and Route APIs
   - Real-time traffic data
   - Road condition updates
   - Weather impact data

3. Toll Calculation Services
   - Electronic toll systems
   - Country-specific calculators
   - Special permit systems

### Business Intelligence
1. Historical Data Analysis
   - Route performance metrics
   - Cost trend analysis
   - Seasonal patterns

2. Market Rate Integration
   - Competitor rate monitoring
   - Market demand indicators
   - Regional price variations

## Implementation Priority

### High Priority
1. Real-time fuel price integration
2. Accurate toll calculation services
3. Dynamic route optimization
4. Complex rest period calculations
5. Vehicle-specific consumption models

### Medium Priority
1. Weather impact integration
2. Loading/unloading time optimization
3. Temperature control cost modeling
4. Multiple driver scenarios
5. Maintenance cost refinement

### Low Priority
1. Historical data analysis
2. Market rate integration
3. Seasonal variation modeling
4. Training cost allocation
5. Administrative overhead refinement

## Notes for Implementation

1. Data Sources
   - Identify reliable APIs for real-time data
   - Establish data update frequencies
   - Define fallback mechanisms

2. Integration Strategy
   - Prioritize critical components
   - Maintain backwards compatibility
   - Plan for graceful degradation

3. Testing Requirements
   - Develop comprehensive test scenarios
   - Include edge cases
   - Validate against real-world data

4. Documentation Needs
   - API integration guides
   - Configuration manuals
   - Rate update procedures
