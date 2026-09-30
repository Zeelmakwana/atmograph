from app.services.operational_intelligence_service import OperationalIntelligenceService


def test_operational_intelligence_empty_payload_is_safe():
    result = OperationalIntelligenceService.build({})
    assert result["operational_timeline"]["production_status"] == "RUNNING"
    assert result["operational_timeline"]["components"] == []


def test_operational_intelligence_hamburg_shape():
    raw = {
        "event": {"id": 51, "source": "manual"},
        "business_supply_chain": {
            "summary": {
                "gross_lost_supply": 18000,
                "alternative_recovery": 5000,
                "gross_shortage": 13000,
                "net_shortage": 0,
                "max_delay_days": 10,
                "max_route_disruption_delay_days": 10,
                "production_stop": False,
            },
            "simulation": {
                "simulations": [
                    {
                        "supplier": {"supplier_id": "SUP001"},
                        "simulation": {
                            "components": [
                                {
                                    "component_id": "CMP001",
                                    "component_name": "Microcontroller",
                                    "plant_id": "PLANT001",
                                    "inventory_quantity": 18000,
                                    "daily_demand": 800,
                                    "alternative_recovery": 3000,
                                    "gross_shortage": 7000,
                                    "net_shortage": 0,
                                    "estimated_delay_days": 10,
                                    "alternative_suppliers": [
                                        {"recoverable_supply_units": 3000, "lead_time_days": 18}
                                    ],
                                },
                                {
                                    "component_id": "CMP003",
                                    "component_name": "Control Board",
                                    "plant_id": "PLANT001",
                                    "inventory_quantity": 9000,
                                    "daily_demand": 1500,
                                    "alternative_recovery": 2000,
                                    "gross_shortage": 6000,
                                    "net_shortage": 0,
                                    "estimated_delay_days": 10,
                                    "alternative_suppliers": [
                                        {"recoverable_supply_units": 2000, "lead_time_days": 7}
                                    ],
                                },
                            ],
                            "products": [
                                {"product_id": "PROD001", "component_id": "CMP001", "plant_id": "PLANT001"},
                            ],
                        },
                    }
                ]
            },
        },
    }

    result = OperationalIntelligenceService.build(raw)
    timeline = result["operational_timeline"]

    assert timeline["production_status"] in {"BUFFERED", "AT_RISK"}
    assert timeline["summary"]["gross_lost_supply"] == 18000
    assert timeline["summary"]["alternative_recovery"] == 5000
    assert timeline["summary"]["net_shortage"] == 0
    assert len(timeline["components"]) == 2
    assert result["operational_audit"]["ml_override"] is False
