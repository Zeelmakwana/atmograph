from __future__ import annotations

from app.api.routes.news_intelligence import (
    _build_unified_intelligence,
)


def test_unified_intelligence_contract():

    raw = {
        "success": True,
        "event_id": 101,
        "graph_id": "event_101",
        "message": "ok",

        "event": {
            "id": 101,
            "title": "Hamburg disruption",
            "description": "Port disruption",
            "source": "manual",
            "event_type": "port_disruption",
            "location": "Hamburg",
            "severity": "high",
            "status": "active",
        },

        "nlp": {
            "event_type": "port_disruption",
            "severity": "high",
            "locations": [
                "Hamburg"
            ],
            "entities": [
                "Global Components Ltd"
            ],
        },

        "business_supply_chain": {
            "matched_suppliers": [
                {
                    "supplier_id": "SUP001",
                    "name": (
                        "Global Components Ltd"
                    ),
                }
            ],

            "simulation": {
                "success": True,

                "suppliers": [
                    {
                        "supplier_id": "SUP001",
                        "name": (
                            "Global Components Ltd"
                        ),
                    }
                ],

                "simulations": [
                    {
                        "summary": {
                            "affected_components": 2,
                            "affected_products": 2,
                            "affected_plants": 1,
                            "gross_lost_supply": 18000,
                            "alternative_recovery": 5000,
                            "gross_shortage": 13000,
                            "net_shortage": 0,
                            "max_delay_days": 24,
                            "max_route_disruption_delay_days": 10,
                            "max_risk_score": 60,
                            "production_stop": False,
                        }
                    }
                ],

                "summary": {
                    "affected_components": 2,
                    "affected_products": 2,
                    "affected_plants": 1,
                    "gross_lost_supply": 18000,
                    "alternative_recovery": 5000,
                    "gross_shortage": 13000,
                    "net_shortage": 0,
                    "max_delay_days": 24,
                    "max_route_disruption_delay_days": 10,
                    "max_risk_score": 60,
                    "production_stop": False,
                },
            },
        },

        "prediction": {
            "base_prediction": {
                "risk_score": 55,
                "risk_level": "high",
                "confidence": 0.8,
            }
        },
    }

    result = (
        _build_unified_intelligence(
            raw
        )
    )

    assert result[
        "success"
    ] is True

    assert result[
        "event_id"
    ] == 101

    assert result[
        "graph_id"
    ] == "event_101"

    intelligence = result[
        "intelligence"
    ]

    assert (
        intelligence[
            "event_understanding"
        ][
            "location"
        ]
        == "Hamburg"
    )

    impact = intelligence[
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

    assert (
        impact[
            "max_route_disruption_delay_days"
        ]
        == 10
    )

    assert (
        intelligence[
            "risk"
        ][
            "score"
        ]
        == 60
    )

    assert (
        intelligence[
            "risk"
        ][
            "level"
        ]
        == "high"
    )

    assert isinstance(
        intelligence[
            "recommendations"
        ],
        list,
    )


def test_unified_contract_without_business_data():

    raw = {
        "success": True,
        "event_id": 1,
        "graph_id": "event_1",
        "event": {
            "id": 1,
            "title": "Test event",
            "description": "Test",
            "source": "manual",
            "event_type": (
                "supply_chain_disruption"
            ),
            "location": None,
            "severity": "medium",
            "status": "active",
        },
        "nlp": {},
        "business_supply_chain": {},
        "prediction": None,
    }

    result = (
        _build_unified_intelligence(
            raw
        )
    )

    assert result[
        "success"
    ] is True

    assert (
        result[
            "intelligence"
        ][
            "business_impact"
        ][
            "net_shortage"
        ]
        == 0
    )

    assert (
        result[
            "intelligence"
        ][
            "risk"
        ][
            "level"
        ]
        == "unknown"
    ) 