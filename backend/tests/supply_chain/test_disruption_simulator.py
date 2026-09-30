from __future__ import annotations

import pytest

from app.core.database import SessionLocal
from app.services.supply_chain.disruption_simulator import (
    DisruptionSimulator,
)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def simulator(db):
    return DisruptionSimulator(db)


# ============================================================
# SUPPLIER
# ============================================================


def test_known_supplier(simulator):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    assert result["success"] is True
    assert result["supplier"]["supplier_id"] == "SUP001"
    assert result["supplier"]["name"] == (
        "Global Components Ltd"
    )


def test_unknown_supplier(simulator):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP999",
    )

    assert result["success"] is False
    assert "Supplier not found" in result["error"]


# ============================================================
# BASIC SUPPLIER FAILURE
# ============================================================


def test_supplier_failure_returns_components(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    assert result["success"] is True

    components = result["components"]

    assert len(components) > 0

    component_ids = {
        item["component_id"]
        for item in components
    }

    assert "CMP001" in component_ids
    assert "CMP003" in component_ids


# ============================================================
# LOST SUPPLY
# ============================================================


def test_supplier_failure_calculates_lost_supply(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    components = {
        item["component_id"]: item
        for item in result["components"]
    }

    assert components["CMP001"][
        "gross_lost_supply"
    ] == pytest.approx(
        10000.0
    )

    assert components["CMP003"][
        "gross_lost_supply"
    ] == pytest.approx(
        8000.0
    )


# ============================================================
# INVENTORY
# ============================================================


def test_inventory_is_loaded(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    components = {
        item["component_id"]: item
        for item in result["components"]
    }

    assert components["CMP001"][
        "inventory_quantity"
    ] == pytest.approx(
        18000.0
    )

    assert components["CMP003"][
        "inventory_quantity"
    ] == pytest.approx(
        9000.0
    )


# ============================================================
# DEMAND
# ============================================================


def test_product_demand_is_resolved(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    components = {
        item["component_id"]: item
        for item in result["components"]
    }

    cmp001 = components["CMP001"]
    cmp003 = components["CMP003"]

    assert cmp001["daily_demand"] == pytest.approx(
        800.0
    )

    assert cmp003["daily_demand"] == pytest.approx(
        1500.0
    )

    assert len(
        cmp001["product_demands"]
    ) >= 1

    assert len(
        cmp003["product_demands"]
    ) >= 2


# ============================================================
# INVENTORY COVERAGE
# ============================================================


def test_inventory_coverage(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    components = {
        item["component_id"]: item
        for item in result["components"]
    }

    assert components["CMP001"][
        "inventory_coverage_days"
    ] == pytest.approx(
        22.5
    )

    assert components["CMP003"][
        "inventory_coverage_days"
    ] == pytest.approx(
        6.0
    )


# ============================================================
# INVENTORY PROTECTION
# ============================================================


def test_inventory_protects_current_demo_supply_chain(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    components = result["components"]

    for component in components:
        assert component[
            "net_shortage"
        ] == pytest.approx(
            0.0
        )

        assert component[
            "production_stop"
        ] is False


# ============================================================
# PRODUCT IMPACT
# ============================================================


def test_products_are_returned(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    products = result["products"]

    assert len(products) >= 1

    product_ids = {
        item["product_id"]
        for item in products
    }

    assert "PROD001" in product_ids
    assert "PROD002" in product_ids


def test_products_are_buffered_when_inventory_absorbs_loss(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    products = result["products"]

    assert len(products) > 0

    for product in products:
        assert product[
            "production_stop"
        ] is False


# ============================================================
# PLANT IMPACT
# ============================================================


def test_plant_impact_is_returned(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    plants = result["plants"]

    assert len(plants) >= 1

    plant_ids = {
        item["plant_id"]
        for item in plants
    }

    assert "PLANT001" in plant_ids


# ============================================================
# SUMMARY
# ============================================================


def test_summary_matches_components(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    summary = result["summary"]

    assert summary[
        "affected_components"
    ] == len(
        result["components"]
    )

    assert summary[
        "affected_products"
    ] == len(
        result["products"]
    )

    assert summary[
        "affected_plants"
    ] == len(
        result["plants"]
    )

    assert summary[
        "gross_lost_supply"
    ] == pytest.approx(
        18000.0
    )


# ============================================================
# ROUTE — NO EVENT
# ============================================================


def test_route_has_no_disruption_without_event(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    route = result["route_impact"]

    assert route["routes_known"] is True

    assert route[
        "additional_disruption_delay_days"
    ] == pytest.approx(
        0.0
    )

    assert route[
        "route_delay_days"
    ] == pytest.approx(
        0.0
    )


# ============================================================
# ROUTE — HAMBURG
# ============================================================


def test_hamburg_disruption_route_timing(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="high",
        event_type="supply_chain_disruption",
    )

    route = result["route_impact"]

    assert route["success"] is True
    assert route["routes_known"] is True
    assert route["location_match"] is True
    assert route["disrupted_routes"] == 1

    assert route[
        "normal_transit_days"
    ] == pytest.approx(
        14.0
    )

    assert route[
        "additional_disruption_delay_days"
    ] == pytest.approx(
        10.0
    )

    assert route[
        "effective_route_time_days"
    ] == pytest.approx(
        24.0
    )

    # Backward compatibility:
    # delay means EXTRA delay, not total transit.
    assert route[
        "route_delay_days"
    ] == pytest.approx(
        10.0
    )

    assert route[
        "effective_delay_days"
    ] == pytest.approx(
        24.0
    )


def test_hamburg_route_contains_correct_values(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="high",
        event_type="supply_chain_disruption",
    )

    routes = result[
        "route_impact"
    ]["routes"]

    assert len(routes) == 1

    route = routes[0]

    assert route[
        "route_id"
    ] == "ROUTE001"

    assert route[
        "normal_transit_days"
    ] == pytest.approx(
        14.0
    )

    assert route[
        "additional_disruption_delay_days"
    ] == pytest.approx(
        10.0
    )

    assert route[
        "effective_route_time_days"
    ] == pytest.approx(
        24.0
    )

    assert route[
        "route_delay_days"
    ] == pytest.approx(
        10.0
    )

    assert route[
        "route_disruption_delay_days"
    ] == pytest.approx(
        10.0
    )

    assert route[
        "effective_delay_days"
    ] == pytest.approx(
        24.0
    )


# ============================================================
# COMPONENT ROUTE PROPAGATION
# ============================================================


def test_route_delay_reaches_component(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="high",
        event_type="supply_chain_disruption",
    )

    components = result["components"]

    assert len(components) > 0

    for component in components:

        assert component[
            "route_transit_days"
        ] == pytest.approx(
            14.0
        )

        assert component[
            "route_disruption_delay_days"
        ] == pytest.approx(
            10.0
        )

        assert component[
            "effective_route_time_days"
        ] == pytest.approx(
            24.0
        )

        assert component[
            "estimated_delay_days"
        ] >= 10.0


# ============================================================
# NORMAL TRANSIT MUST NOT BECOME DISRUPTION DELAY
# ============================================================


def test_normal_transit_is_not_disruption_delay(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location=None,
        severity="high",
        event_type=None,
    )

    route = result["route_impact"]

    assert route[
        "normal_transit_days"
    ] == pytest.approx(
        14.0
    )

    assert route[
        "additional_disruption_delay_days"
    ] == pytest.approx(
        0.0
    )

    assert route[
        "route_delay_days"
    ] == pytest.approx(
        0.0
    )


# ============================================================
# UNKNOWN LOCATION
# ============================================================


def test_unknown_location_does_not_fabricate_disruption(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Singapore",
        severity="high",
        event_type="port_disruption",
    )

    route = result["route_impact"]

    assert route["routes_known"] is True

    assert route[
        "location_match"
    ] is False

    assert route[
        "disrupted_routes"
    ] == 0

    assert route[
        "additional_disruption_delay_days"
    ] == pytest.approx(
        0.0
    )


# ============================================================
# EXPLICIT ROUTE STATUS
# ============================================================


def test_route_semantics_are_consistent(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="critical",
        event_type="port_disruption",
    )

    route = result[
        "route_impact"
    ]

    normal = route[
        "normal_transit_days"
    ]

    disruption = route[
        "additional_disruption_delay_days"
    ]

    effective = route[
        "effective_route_time_days"
    ]

    assert effective == pytest.approx(
        normal + disruption
    )

    assert route[
        "route_delay_days"
    ] == pytest.approx(
        disruption
    )

    assert route[
        "effective_delay_days"
    ] == pytest.approx(
        effective
    )


# ============================================================
# RISK
# ============================================================


def test_risk_is_present(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    for component in result["components"]:

        assert (
            "risk_score"
            in component
        )

        assert (
            "risk_level"
            in component
        )

        assert 0 <= component[
            "risk_score"
        ] <= 100

        assert component[
            "risk_level"
        ] in {
            "low",
            "medium",
            "high",
            "critical",
        }


# ============================================================
# CONFIDENCE
# ============================================================


def test_confidence_is_valid(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
    )

    for component in result["components"]:

        confidence = component[
            "confidence"
        ]

        assert 0 <= confidence <= 1


# ============================================================
# EVENT CONTEXT
# ============================================================


def test_event_context_is_forwarded(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="high",
        event_type="port_disruption",
    )

    assert result[
        "scenario"
    ] == {
        "disruption_location": "Hamburg",
        "severity": "high",
        "event_type": "port_disruption",
    }


# ============================================================
# SUMMARY DELAY SEMANTICS
# ============================================================


def test_summary_delay_is_not_normal_transit(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="high",
        event_type="port_disruption",
    )

    summary = result["summary"]

    assert summary[
        "max_route_disruption_delay_days"
    ] == pytest.approx(
        10.0
    )

    # Delay should never become 24 simply because
    # normal transit is 14 and event delay is 10.
    assert summary[
        "max_route_disruption_delay_days"
    ] != pytest.approx(
        24.0
    )


# ============================================================
# FULL HAMBURG BUSINESS SCENARIO
# ============================================================


def test_full_hamburg_scenario(
    simulator,
):
    result = simulator.simulate_supplier_failure(
        supplier_id="SUP001",
        disruption_location="Hamburg",
        severity="high",
        event_type="supply_chain_disruption",
    )

    assert result["success"] is True

    summary = result["summary"]

    assert summary[
        "affected_components"
    ] == 2

    assert summary[
        "affected_plants"
    ] == 1

    assert summary[
        "gross_lost_supply"
    ] == pytest.approx(
        18000.0
    )

    assert summary[
        "alternative_recovery"
    ] >= 0

    assert summary[
        "net_shortage"
    ] >= 0

    assert summary[
        "max_route_disruption_delay_days"
    ] == pytest.approx(
        10.0
    )

    assert (
        "production_stop"
        in summary
    )