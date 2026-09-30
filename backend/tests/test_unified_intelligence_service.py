from app.services.unified_intelligence_service import (
    UnifiedIntelligenceService,
)


def test_unified_intelligence_hamburg_contract():

    raw = {
        "success": True,

        "event": {
            "id": 42,
            "event_id": 42,
            "title": (
                "Hamburg port disruption affects "
                "Global Components Ltd"
            ),
            "description": (
                "Hamburg disruption."
            ),
            "source": "manual",
            "event_type": "supply_chain_disruption",
            "location": "Hamburg",
            "severity": "high",
            "status": "active",
        },

        "nlp": {
            "event_type": "supply_chain_disruption",
            "severity": "high",
            "locations": [
                "Hamburg",
            ],
        },

        "business_supply_chain": {
            "matched_suppliers": [
                {
                    "supplier_id": "SUP001",
                    "name": "Global Components Ltd",
                }
            ],

            "simulation": {
                "simulations": [
                    {
                        "supplier": {
                            "supplier_id": "SUP001",
                            "name": "Global Components Ltd",
                        },

                        "simulation": {
                            "success": True,

                            "route_impact": {
                                "routes_known": True,
                                "location_match": True,
                                "routes_analyzed": 1,
                                "disrupted_routes": 1,
                                "normal_transit_days": 14,
                                "additional_disruption_delay_days": 10,
                                "effective_route_time_days": 24,
                                "route_delay_days": 10,
                                "effective_delay_days": 24,
                            },

                            "components": [
                                {
                                    "component_id": "CMP001",
                                    "gross_lost_supply": 10000,
                                    "alternative_recovery": 3000,
                                    "gross_shortage": 7000,
                                },
                                {
                                    "component_id": "CMP003",
                                    "gross_lost_supply": 8000,
                                    "alternative_recovery": 2000,
                                    "gross_shortage": 6000,
                                },
                            ],

                            "products": [
                                {
                                    "product_id": "PROD001",
                                    "exposure_status": "route_delayed",
                                },
                                {
                                    "product_id": "PROD002",
                                    "exposure_status": "route_delayed",
                                },
                                {
                                    "product_id": "PROD003",
                                    "exposure_status": "route_delayed",
                                },
                            ],

                            "plants": [
                                {
                                    "plant_id": "PLANT001",
                                },
                            ],

                            "summary": {
                                "affected_components": 2,
                                "affected_products": 3,
                                "affected_plants": 1,
                                "gross_lost_supply": 18000,
                                "alternative_recovery": 5000,
                                "gross_shortage": 13000,
                                "net_shortage": 0,
                                "products_buffered": 0,
                                "products_route_delayed": 3,
                                "products_with_shortage": 0,
                                "production_stop": False,
                                "max_delay_days": 10,
                                "max_risk_score": 70,
                            },
                        },
                    }
                ]
            },
        },

        "prediction": {
            "base_prediction": {
                "risk_score": 75,
                "risk_level": "critical",
                "estimated_delay_days": 10,
            },
            "gnn_prediction": {
                "risk_score": 68.05,
                "model": "AtmoGraphGNN",
                "model_loaded": True,
            },
            "hybrid_prediction": {
                "risk_score": 70.83,
                "risk_level": "high",
            },
        },
    }

    result = UnifiedIntelligenceService.build(
        raw
    )

    assert result["version"] == "1.0"

    assert (
        result["event"]["event_id"]
        == 42
    )

    assert (
        result["event"]["location"]
        == "Hamburg"
    )

    assert (
        result[
            "supplier_exposure"
        ][
            "matched_count"
        ]
        == 1
    )

    impact = result[
        "business_impact"
    ]

    assert (
        impact[
            "affected_components"
        ]
        == 2
    )

    assert (
        impact[
            "affected_products"
        ]
        == 3
    )

    assert (
        impact[
            "gross_lost_supply"
        ]
        == 18000
    )

    assert (
        impact[
            "alternative_recovery"
        ]
        == 5000
    )

    assert (
        impact[
            "net_shortage"
        ]
        == 0
    )

    route = result[
        "route_impact"
    ]

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
        == 10
    )

    assert (
        route[
            "effective_route_time_days"
        ]
        == 24
    )

    assert (
        route[
            "route_delay_days"
        ]
        == 10
    )

    assert (
        route[
            "effective_delay_days"
        ]
        == 24
    )

    assert (
        result[
            "risk"
        ][
            "score"
        ]
        == 70
    )

    assert (
        result[
            "prediction"
        ][
            "risk_score"
        ]
        == 70.83
    )

    assert (
        len(
            result[
                "recommendations"
            ]
        )
        > 0
    )


def test_unknown_location_has_no_added_route_delay():

    raw = {
        "success": True,

        "event": {
            "id": 99,
            "title": "Unknown location disruption",
            "description": "Test",
            "source": "manual",
            "event_type": "port_disruption",
            "location": "UnknownPortXYZ",
            "severity": "high",
            "status": "active",
        },

        "business_supply_chain": {
            "simulation": {
                "simulations": [
                    {
                        "supplier": {
                            "supplier_id": "SUP001",
                            "name": "Global Components Ltd",
                        },
                        "simulation": {
                            "success": True,

                            "route_impact": {
                                "routes_known": True,
                                "location_match": False,
                                "routes_analyzed": 1,
                                "disrupted_routes": 0,
                                "normal_transit_days": 14,
                                "additional_disruption_delay_days": 0,
                                "effective_route_time_days": 14,
                                "route_delay_days": 0,
                                "effective_delay_days": 14,
                            },

                            "components": [],

                            "summary": {
                                "affected_components": 0,
                                "affected_products": 0,
                                "affected_plants": 0,
                                "gross_lost_supply": 0,
                                "alternative_recovery": 0,
                                "gross_shortage": 0,
                                "net_shortage": 0,
                                "production_stop": False,
                            },
                        },
                    }
                ]
            }
        },
    }

    result = UnifiedIntelligenceService.build(
        raw
    )

    route = result[
        "route_impact"
    ]

    assert (
        route[
            "routes_known"
        ]
        is True
    )

    assert (
        route[
            "location_match"
        ]
        is False
    )

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
        == 0
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


def test_empty_response_is_safe():

    result = UnifiedIntelligenceService.build(
        {}
    )

    assert result["version"] == "1.0"

    assert (
        result[
            "business_impact"
        ][
            "affected_components"
        ]
        == 0
    )

    assert (
        result[
            "route_impact"
        ][
            "normal_transit_days"
        ]
        == 0
    )

    assert (
        result[
            "route_impact"
        ][
            "additional_disruption_delay_days"
        ]
        == 0
    )

    assert (
        result[
            "route_impact"
        ][
            "effective_route_time_days"
        ]
        == 0
    )
