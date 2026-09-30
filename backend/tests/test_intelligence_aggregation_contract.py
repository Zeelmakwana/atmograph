from app.services.intelligence_pipeline import (
    IntelligencePipeline,
)


def test_business_summary_aggregates_route_metrics():
    payload = {
        "success": True,
        "simulations": [
            {
                "supplier": {
                    "supplier_id": "SUP001",
                },
                "simulation": {
                    "success": True,
                    "components": [
                        {
                            "component_id": "CMP001",
                            "route_transit_days": 14,
                            "route_disruption_delay_days": 10,
                            "effective_route_time_days": 24,
                            "gross_lost_supply": 10000,
                            "alternative_recovery": 3000,
                            "gross_shortage": 7000,
                            "net_shortage": 0,
                            "risk_score": 70,
                        },
                        {
                            "component_id": "CMP003",
                            "route_transit_days": 14,
                            "route_disruption_delay_days": 10,
                            "effective_route_time_days": 24,
                            "gross_lost_supply": 8000,
                            "alternative_recovery": 2000,
                            "gross_shortage": 6000,
                            "net_shortage": 0,
                            "risk_score": 70,
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
                        "max_delay_days": 10,
                        "max_route_disruption_delay_days": 10,
                        "max_risk_score": 70,
                        "production_stop": False,
                        "products_buffered": 0,
                        "products_route_delayed": 3,
                        "products_with_shortage": 0,
                    },
                },
            }
        ],
    }

    result = (
        IntelligencePipeline
        ._aggregate_business_impact(
            payload
        )
    )

    assert result["affected_components"] == 2
    assert result["affected_products"] == 3
    assert result["affected_plants"] == 1

    assert result["gross_lost_supply"] == 18000
    assert result["alternative_recovery"] == 5000
    assert result["gross_shortage"] == 13000
    assert result["net_shortage"] == 0

    assert result["normal_transit_days"] == 14
    assert (
        result[
            "additional_disruption_delay_days"
        ]
        == 10
    )
    assert result["effective_route_time_days"] == 24

    assert result["max_delay_days"] == 10
    assert (
        result[
            "max_route_disruption_delay_days"
        ]
        == 10
    )

    assert result["max_risk_score"] == 70
    assert result["production_stop"] is False

    assert result["products_route_delayed"] == 3


def test_business_summary_does_not_treat_transit_as_delay():
    payload = {
        "success": True,
        "simulations": [
            {
                "simulation": {
                    "success": True,
                    "components": [
                        {
                            "component_id": "CMP001",
                            "route_transit_days": 14,
                            "route_disruption_delay_days": 0,
                            "effective_route_time_days": 14,
                            "gross_lost_supply": 10000,
                            "alternative_recovery": 3000,
                            "gross_shortage": 7000,
                            "net_shortage": 0,
                            "risk_score": 20,
                        },
                    ],
                    "products": [],
                    "plants": [],
                    "summary": {
                        "affected_components": 1,
                        "affected_products": 0,
                        "affected_plants": 0,
                        "gross_lost_supply": 10000,
                        "alternative_recovery": 3000,
                        "gross_shortage": 7000,
                        "net_shortage": 0,
                        "max_delay_days": 0,
                        "max_route_disruption_delay_days": 0,
                        "max_risk_score": 20,
                        "production_stop": False,
                    },
                }
            }
        ],
    }

    result = (
        IntelligencePipeline
        ._aggregate_business_impact(
            payload
        )
    )

    assert result["normal_transit_days"] == 14
    assert (
        result[
            "additional_disruption_delay_days"
        ]
        == 0
    )
    assert result["effective_route_time_days"] == 14
    assert result["max_route_disruption_delay_days"] == 0
    assert result["max_delay_days"] == 0


def test_empty_business_summary_has_canonical_route_fields():
    result = (
        IntelligencePipeline
        ._aggregate_business_impact(
            {
                "success": False,
                "simulations": [],
            }
        )
    )

    assert result["normal_transit_days"] == 0
    assert (
        result[
            "additional_disruption_delay_days"
        ]
        == 0
    )
    assert result["effective_route_time_days"] == 0
    assert result["max_route_disruption_delay_days"] == 0
