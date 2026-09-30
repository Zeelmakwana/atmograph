from __future__ import annotations

import pytest

from app.services.supply_chain.resilience_service import (
    SupplyChainResilienceService,
)


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        if isinstance(
            self.result,
            list,
        ):
            return (
                self.result[0]
                if self.result
                else None
            )

        return self.result

    def all(self):
        if isinstance(
            self.result,
            list,
        ):
            return self.result

        if self.result is None:
            return []

        return [self.result]


class FakeDB:
    def __init__(
        self,
        supplier,
        allocations,
        components=None,
        plants=None,
        suppliers=None,
    ):
        self.supplier = supplier
        self.allocations = allocations
        self.components = components or []
        self.plants = plants or []
        self.suppliers = suppliers or []

    def query(self, model):

        model_name = getattr(
            model,
            "__name__",
            "",
        )

        if model_name == "BusinessSupplier":

            if self.supplier is not None:
                return FakeQuery(
                    self.supplier
                )

            return FakeQuery(
                self.suppliers
            )

        if model_name == "SupplyAllocation":
            return FakeQuery(
                self.allocations
            )

        if model_name == "Component":
            return FakeQuery(
                self.components
            )

        if model_name == "Plant":
            return FakeQuery(
                self.plants
            )

        return FakeQuery(None)


class Obj:
    def __init__(
        self,
        **kwargs,
    ):
        self.__dict__.update(kwargs)


def test_empty_supplier_allocations():

    supplier = Obj(
        supplier_id="SUP001",
        supplier_name=(
            "Global Components Ltd"
        ),
        country="Germany",
        city="Hamburg",
        location_known=True,
    )

    db = FakeDB(
        supplier=supplier,
        allocations=[],
    )

    result = (
        SupplyChainResilienceService(
            db
        ).analyze_supplier(
            "SUP001"
        )
    )

    assert result["success"] is True

    assert (
        result["analysis"][
            "summary"
        ]["affected_components"]
        == 0
    )

    assert (
        result["analysis"][
            "resilience_level"
        ]
        == "critical_risk"
    )


def test_missing_supplier():

    db = FakeDB(
        supplier=None,
        allocations=[],
    )

    result = (
        SupplyChainResilienceService(
            db
        ).analyze_supplier(
            "UNKNOWN"
        )
    )

    assert result["success"] is False

    assert "not found" in (
        result["error"].lower()
    )


def test_number_helper():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    assert (
        service._number(10)
        == 10.0
    )

    assert (
        service._number(None)
        == 0.0
    )

    assert (
        service._number("5")
        == 5.0
    )


def test_spare_capacity_helper():

    allocation = Obj(
        spare_capacity_units=3000
    )

    result = (
        SupplyChainResilienceService
        ._get_spare_capacity(
            allocation
        )
    )

    assert result == 3000.0


def test_missing_spare_capacity_defaults_to_zero():

    allocation = Obj()

    result = (
        SupplyChainResilienceService
        ._get_spare_capacity(
            allocation
        )
    )

    assert result == 0.0


def test_negative_spare_capacity_is_zero():

    allocation = Obj(
        spare_capacity_units=-100
    )

    result = (
        SupplyChainResilienceService
        ._get_spare_capacity(
            allocation
        )
    )

    assert result == 0.0


def test_invalid_spare_capacity_is_zero():

    allocation = Obj(
        spare_capacity_units="invalid"
    )

    result = (
        SupplyChainResilienceService
        ._get_spare_capacity(
            allocation
        )
    )

    assert result == 0.0


def test_resilience_level():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    assert (
        service._resilience_level(80)
        == "resilient"
    )

    assert (
        service._resilience_level(55)
        == "moderate"
    )

    assert (
        service._resilience_level(30)
        == "high_risk"
    )

    assert (
        service._resilience_level(10)
        == "critical_risk"
    )


def test_resilience_level_boundaries():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    assert (
        service._resilience_level(70)
        == "resilient"
    )

    assert (
        service._resilience_level(45)
        == "moderate"
    )

    assert (
        service._resilience_level(20)
        == "high_risk"
    )


def test_allocation_status():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    assert (
        service._allocation_status(
            100,
            3,
        )
        == "resilient"
    )

    assert (
        service._allocation_status(
            50,
            1,
        )
        == "moderate"
    )

    assert (
        service._allocation_status(
            0,
            0,
        )
        == "single_source"
    )


def test_resilience_score_uses_recovery():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    results = [
        {
            "lost_supply_units": 10000,
            "recoverable_supply_units": 5000,
            "alternative_supplier_count": 1,
            "criticality": "high",
        }
    ]

    score = (
        service._calculate_resilience_score(
            results
        )
    )

    assert score >= 0
    assert score <= 100


def test_summary():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    results = [
        {
            "lost_supply_units": 10000,
            "recoverable_supply_units": 3000,
            "alternative_supplier_count": 1,
            "criticality": "critical",
            "resilience_status": (
                "moderate"
            ),
        },
        {
            "lost_supply_units": 8000,
            "recoverable_supply_units": 2000,
            "alternative_supplier_count": 1,
            "criticality": "high",
            "resilience_status": (
                "moderate"
            ),
        },
    ]

    summary = (
        service._build_summary(
            results
        )
    )

    assert (
        summary[
            "gross_lost_supply_units"
        ]
        == 18000
    )

    assert (
        summary[
            "alternative_recovery_units"
        ]
        == 5000
    )

    assert (
        summary[
            "unrecovered_supply_units"
        ]
        == 13000
    )

    assert (
        summary[
            "recovery_percentage"
        ]
        == pytest.approx(
            27.78,
            abs=0.01,
        )
    )

    assert (
        summary[
            "components_with_alternatives"
        ]
        == 2
    )

    assert (
        summary[
            "single_source_components"
        ]
        == 0
    )


def test_empty_summary():

    service = (
        SupplyChainResilienceService(
            None
        )
    )

    summary = (
        service._empty_summary()
    )

    assert (
        summary[
            "affected_components"
        ]
        == 0
    )

    assert (
        summary[
            "gross_lost_supply_units"
        ]
        == 0.0
    )

    assert (
        summary[
            "alternative_recovery_units"
        ]
        == 0.0
    )