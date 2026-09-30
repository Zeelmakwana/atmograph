from __future__ import annotations

from app.core.database import SessionLocal
from app.services.supply_chain.disruption_simulator import (
    DisruptionSimulator,
)


def test_hamburg_route_timing_contract():
    db = SessionLocal()

    try:
        result = (
            DisruptionSimulator(db)
            .simulate_supplier_failure(
                supplier_id="SUP001",
                disruption_location="Hamburg",
                severity="high",
                event_type="port_disruption",
            )
        )

        assert result["success"] is True

        route = result["route_impact"]

        assert route["routes_known"] is True
        assert route["location_match"] is True
        assert route["disrupted_routes"] == 1

        # Normal transit is NOT disruption delay.
        assert route["normal_transit_days"] == 14
        assert (
            route[
                "additional_disruption_delay_days"
            ]
            == 10
        )

        # 14 normal + 10 additional = 24 total route time.
        assert (
            route[
                "effective_route_time_days"
            ]
            == 24
        )

        # Backward-compatible fields.
        assert route["route_delay_days"] == 10
        assert route["effective_delay_days"] == 24

        for component in result["components"]:
            assert (
                component[
                    "route_transit_days"
                ]
                == 14
            )

            assert (
                component[
                    "route_disruption_delay_days"
                ]
                == 10
            )

            assert (
                component[
                    "effective_route_time_days"
                ]
                == 24
            )

            # Estimated business delay is additional disruption
            # delay, not the normal 14-day transit.
            assert (
                component[
                    "estimated_delay_days"
                ]
                == 10
            )

    finally:
        db.close()


def test_critical_event_uses_critical_delay():
    db = SessionLocal()

    try:
        result = (
            DisruptionSimulator(db)
            .simulate_supplier_failure(
                supplier_id="SUP001",
                disruption_location="Hamburg",
                severity="critical",
                event_type="port_disruption",
            )
        )

        assert result["success"] is True

        route = result["route_impact"]

        assert (
            route[
                "normal_transit_days"
            ]
            == 14
        )

        assert (
            route[
                "additional_disruption_delay_days"
            ]
            == 14
        )

        assert (
            route[
                "effective_route_time_days"
            ]
            == 28
        )

        # Critical delay must not be confused with transit.
        assert (
            route[
                "route_delay_days"
            ]
            == 14
        )

    finally:
        db.close()


def test_unknown_location_does_not_create_route_delay():
    db = SessionLocal()

    try:
        result = (
            DisruptionSimulator(db)
            .simulate_supplier_failure(
                supplier_id="SUP001",
                disruption_location="UnknownPortXYZ",
                severity="high",
                event_type="port_disruption",
            )
        )

        assert result["success"] is True

        route = result["route_impact"]

        assert (
            route[
                "location_match"
            ]
            is False
        )

        assert (
            route[
                "additional_disruption_delay_days"
            ]
            == 0
        )

        # Normal transit still exists as route information.
        assert (
            route[
                "normal_transit_days"
            ]
            == 14
        )

        assert (
            route[
                "effective_route_time_days"
            ]
            == 14
        )

        assert (
            route[
                "route_delay_days"
            ]
            == 0
        )

    finally:
        db.close()