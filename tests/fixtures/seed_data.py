"""Database seed data for development and testing."""
from datetime import datetime, timezone, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session

from src.infrastructure.models import (
    TransportType,
    CostSettings,
    Cargo,
    Route,
    Offer,
    CostHistory,
    CalculationMethod,
    OfferStatus,
)


def seed_transport_types(db: Session) -> List[TransportType]:
    """Seed transport types data."""
    transport_types = [
        TransportType(
            id="standard_truck",
            name="Standard Truck",
            capacity=24000.0,  # 24 tons
            emissions_class="EURO6",
            fuel_consumption_empty=25.0,  # L/100km
            fuel_consumption_loaded=32.0,  # L/100km
            extra_data={"axles": 5, "height_m": 4.0, "length_m": 13.6},
        ),
        TransportType(
            id="eco_truck",
            name="Eco Truck",
            capacity=22000.0,  # 22 tons
            emissions_class="EURO6",
            fuel_consumption_empty=22.0,  # L/100km
            fuel_consumption_loaded=28.0,  # L/100km
            extra_data={"axles": 5, "height_m": 4.0, "length_m": 13.6, "aerodynamic": True},
        ),
        TransportType(
            id="heavy_truck",
            name="Heavy Duty Truck",
            capacity=28000.0,  # 28 tons
            emissions_class="EURO5",
            fuel_consumption_empty=28.0,  # L/100km
            fuel_consumption_loaded=35.0,  # L/100km
            extra_data={"axles": 6, "height_m": 4.0, "length_m": 13.6},
        ),
    ]
    
    for transport in transport_types:
        db.merge(transport)
    db.commit()
    
    return transport_types


def seed_cost_settings(db: Session) -> CostSettings:
    """Seed cost settings data."""
    # Create transport types and cargoes first
    transport_types = seed_transport_types(db)
    cargoes = seed_cargoes(db)
    
    # Create a route using seed_routes
    routes = seed_routes(db, transport_types, cargoes)
    route = routes[0]  # Use the first route
    
    now = datetime.now(timezone.utc)
    cost_settings = CostSettings(
        id="default",
        route_id=route.id,
        version="1.0",
        fuel_rates={
            "diesel": 1.8,  # EUR/L
            "adblue": 0.8,  # EUR/L
        },
        toll_rates={
            "DE": {"standard": 0.187, "eco": 0.178, "heavy": 0.198},  # EUR/km
            "PL": {"standard": 0.095, "eco": 0.090, "heavy": 0.105},
            "CZ": {"standard": 0.108, "eco": 0.102, "heavy": 0.115},
        },
        driver_rates={
            "daily": 200.0,  # EUR/day
            "hourly": 25.0,  # EUR/hour
            "overtime": 35.0,  # EUR/hour
        },
        overhead_rates={
            "maintenance_per_km": 0.15,  # EUR/km
            "insurance_daily": 25.0,     # EUR/day
            "admin_fee": 50.0,          # EUR/route
        },
        maintenance_rates={
            "per_km": 0.12,  # EUR/km
            "per_hour": 5.0,  # EUR/hour
        },
        enabled_components=[
            "fuel",
            "toll",
            "driver",
            "maintenance",
            "overhead"
        ],
        created_at=now,
        modified_at=now,
    )
    
    db.add(cost_settings)
    db.commit()
    
    return cost_settings


def seed_cargoes(db: Session) -> List[Cargo]:
    """Seed cargo data."""
    cargoes = [
        Cargo(
            id="standard_cargo",
            weight=18000.0,  # 18 tons
            value=50000.0,   # EUR
            special_requirements={"temperature_control": False, "loading_type": "side"},
            hazmat=False,
            extra_data={"packaging": "pallets", "pieces": 22},
        ),
        Cargo(
            id="valuable_cargo",
            weight=15000.0,  # 15 tons
            value=150000.0,  # EUR
            special_requirements={"temperature_control": True, "loading_type": "rear"},
            hazmat=False,
            extra_data={"packaging": "containers", "pieces": 12},
        ),
        Cargo(
            id="hazmat_cargo",
            weight=20000.0,  # 20 tons
            value=75000.0,   # EUR
            special_requirements={"temperature_control": False, "loading_type": "rear"},
            hazmat=True,
            extra_data={"hazmat_class": "3", "un_number": "UN1203"},
        ),
    ]
    
    for cargo in cargoes:
        db.merge(cargo)
    db.commit()
    
    return cargoes


def seed_routes(db: Session, transport_types: List[TransportType], cargoes: List[Cargo]) -> List[Route]:
    """Seed route data."""
    base_time = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
    
    routes = [
        Route(
            id="route_standard",
            origin={"latitude": 52.520008, "longitude": 13.404954},  # Berlin
            destination={"latitude": 50.075538, "longitude": 14.437800},  # Prague
            pickup_time=base_time,
            delivery_time=base_time + timedelta(hours=6),
            transport_type=transport_types[0].id,  # standard_truck
            cargo_id=cargoes[0].id,  # standard_cargo
            distance_km=350.0,
            duration_hours=6.0,
            empty_driving={"before_km": 20.0, "after_km": 15.0},
            is_feasible=True,
            status="draft",
            created_at=datetime.now(timezone.utc),
        ),
        Route(
            id="route_eco",
            origin={"latitude": 52.229676, "longitude": 21.012229},  # Warsaw
            destination={"latitude": 50.075538, "longitude": 14.437800},  # Prague
            pickup_time=base_time,
            delivery_time=base_time + timedelta(hours=8),
            transport_type=transport_types[1].id,  # eco_truck
            cargo_id=cargoes[1].id,  # valuable_cargo
            distance_km=520.0,
            duration_hours=8.0,
            empty_driving={"before_km": 30.0, "after_km": 25.0},
            is_feasible=True,
            status="draft",
            created_at=datetime.now(timezone.utc),
        ),
        Route(
            id="route_heavy",
            origin={"latitude": 50.075538, "longitude": 14.437800},  # Prague
            destination={"latitude": 48.208174, "longitude": 16.373819},  # Vienna
            pickup_time=base_time,
            delivery_time=base_time + timedelta(hours=4),
            transport_type=transport_types[2].id,  # heavy_truck
            cargo_id=cargoes[2].id,  # hazmat_cargo
            distance_km=250.0,
            duration_hours=4.0,
            empty_driving={"before_km": 15.0, "after_km": 10.0},
            is_feasible=True,
            status="draft",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    
    for route in routes:
        db.merge(route)
    db.commit()
    
    return routes


def seed_offers(db: Session, routes: List[Route]) -> List[Offer]:
    """Seed offer data."""
    now = datetime.now(timezone.utc)
    
    # Create cost history entries first
    cost_histories = [
        CostHistory(
            id=f"cost_history_{i+1}",
            route_id=route.id,
            calculation_date=now,
            total_cost=total_cost,
            currency="EUR",
            calculation_method=CalculationMethod.STANDARD,
            version="1.0",
            is_final=True,
            cost_components={
                "fuel": total_cost * 0.3,
                "toll": total_cost * 0.2,
                "driver": total_cost * 0.3,
                "maintenance": total_cost * 0.1,
                "overhead": total_cost * 0.1
            },
            settings_snapshot={
                "fuel_rates": {"diesel": 1.8},
                "toll_rates": {"standard": 0.187},
                "driver_rates": {"hourly": 25.0}
            }
        )
        for i, (route, total_cost) in enumerate(zip(routes, [450.0, 680.0, 520.0]))
    ]
    
    for cost_history in cost_histories:
        db.add(cost_history)
    db.flush()

    # Now create the offers
    offers = [
        Offer(
            id="offer_standard",
            route_id=routes[0].id,
            cost_history_id=cost_histories[0].id,
            version="1.0",
            margin=0.15,
            total_cost=450.0,
            final_price=517.50,
            currency="EUR",
            fun_fact="This route crosses through two countries!",
            created_at=now,
            status=OfferStatus.DRAFT
        ),
        Offer(
            id="offer_eco",
            route_id=routes[1].id,
            cost_history_id=cost_histories[1].id,
            version="1.0",
            margin=0.18,
            total_cost=680.0,
            final_price=802.40,
            currency="EUR",
            fun_fact="Using an eco-friendly truck saves 15% on emissions!",
            created_at=now,
            status=OfferStatus.DRAFT
        ),
        Offer(
            id="offer_heavy",
            route_id=routes[2].id,
            cost_history_id=cost_histories[2].id,
            version="1.0",
            margin=0.20,
            total_cost=520.0,
            final_price=624.0,
            currency="EUR",
            fun_fact="This route includes special handling for hazardous materials.",
            created_at=now,
            status=OfferStatus.DRAFT
        ),
    ]
    
    for offer in offers:
        db.merge(offer)
    db.commit()
    
    return offers


def seed_all(db: Session) -> Dict[str, List]:
    """Seed all data in the correct order."""
    transport_types = seed_transport_types(db)
    cost_settings = seed_cost_settings(db)
    cargoes = seed_cargoes(db)
    routes = seed_routes(db, transport_types, cargoes)
    offers = seed_offers(db, routes)
    
    return {
        "transport_types": transport_types,
        "cost_settings": [cost_settings],
        "cargoes": cargoes,
        "routes": routes,
        "offers": offers,
    }
