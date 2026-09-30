from __future__ import annotations

from typing import Any

from app.models.business_supply_chain import (
    BusinessSupplier,
    Component,
    Plant,
    SupplyAllocation,
)


class SupplyChainResilienceService:
    """
    Supplier failure resilience analysis.

    Business rules
    --------------
    1. A supplier failure removes that supplier's allocated capacity.
    2. Alternative recovery comes ONLY from explicitly declared
       spare_capacity_units on alternative supplier allocations.
    3. Existing allocated capacity is not treated as spare capacity.
    4. Plant capacity is not treated as supplier spare capacity.
    5. Lead time is informational here and is not converted into capacity.
    6. Unknown information remains unknown instead of being guessed.

    The service produces deterministic and explainable resilience
    information for the AtmoGraph supply-chain intelligence layer.
    """

    RESILIENT_THRESHOLD = 70.0
    MODERATE_THRESHOLD = 45.0
    HIGH_RISK_THRESHOLD = 20.0

    def __init__(self, db, user_id: int | None = None):
        self.db = db
        self.user_id = user_id

    def _query(self, model):
        query = self.db.query(model)
        if self.user_id is not None:
            query = query.filter(model.user_id == self.user_id)
        return query

    # ============================================================
    # PUBLIC API
    # ============================================================

    def analyze_supplier(
        self,
        supplier_id: str,
    ) -> dict[str, Any]:
        """
        Analyze the supply-chain resilience against failure of
        one supplier.
        """

        supplier = (
            self._query(BusinessSupplier)
            .filter(
                BusinessSupplier.supplier_id
                == str(supplier_id)
            )
            .first()
        )

        # IMPORTANT:
        # Some test doubles / query implementations may return an
        # empty list instead of None. Treat any non supplier-like
        # object as "not found".
        if supplier is None or not hasattr(
            supplier,
            "supplier_id",
        ):
            return {
                "success": False,
                "error": (
                    f"Supplier '{supplier_id}' "
                    "was not found."
                ),
            }

        allocations = (
            self._query(SupplyAllocation)
            .filter(
                SupplyAllocation.supplier_id
                == str(supplier_id)
            )
            .all()
        )

        if not allocations:
            return {
                "success": True,
                "analysis_type": (
                    "supplier_resilience"
                ),
                "supplier": self._supplier_payload(
                    supplier
                ),
                "analysis": {
                    "allocations": [],
                    "summary": self._empty_summary(),
                    "resilience_score": 0.0,
                    "resilience_level": (
                        "critical_risk"
                    ),
                },
            }

        component_results: list[
            dict[str, Any]
        ] = []

        for allocation in allocations:
            component_results.append(
                self._analyze_allocation(
                    failed_supplier_id=str(
                        supplier_id
                    ),
                    allocation=allocation,
                )
            )

        score = self._calculate_resilience_score(
            component_results
        )

        level = self._resilience_level(
            score
        )

        summary = self._build_summary(
            component_results
        )

        return {
            "success": True,
            "analysis_type": (
                "supplier_resilience"
            ),
            "supplier": self._supplier_payload(
                supplier
            ),
            "analysis": {
                "allocations": component_results,
                "summary": summary,
                "resilience_score": round(
                    score,
                    2,
                ),
                "resilience_level": level,
            },
        }

    # ============================================================
    # ALLOCATION ANALYSIS
    # ============================================================

    def _analyze_allocation(
        self,
        failed_supplier_id: str,
        allocation: SupplyAllocation,
    ) -> dict[str, Any]:

        component_id = str(
            allocation.component_id
        )

        plant_id = str(
            allocation.plant_id
        )

        component = (
            self._query(Component)
            .filter(
                Component.component_id
                == component_id
            )
            .first()
        )

        plant = (
            self._query(Plant)
            .filter(
                Plant.plant_id
                == plant_id
            )
            .first()
        )

        lost_supply = self._number(
            allocation.capacity_units
        )

        alternatives = (
            self._query(SupplyAllocation)
            .filter(
                SupplyAllocation.component_id
                == allocation.component_id,
                SupplyAllocation.plant_id
                == allocation.plant_id,
                SupplyAllocation.supplier_id
                != failed_supplier_id,
            )
            .all()
        )

        alternative_results: list[
            dict[str, Any]
        ] = []

        remaining_loss = lost_supply
        total_recovery = 0.0

        for alternative in alternatives:

            spare_capacity = (
                self._get_spare_capacity(
                    alternative
                )
            )

            allocated_capacity = self._number(
                alternative.capacity_units
            )

            recoverable = min(
                spare_capacity,
                remaining_loss,
            )

            remaining_loss = max(
                0.0,
                remaining_loss - recoverable,
            )

            total_recovery += recoverable

            alternative_supplier = (
                self._query(BusinessSupplier)
                .filter(
                    BusinessSupplier.supplier_id
                    == str(
                        alternative.supplier_id
                    )
                )
                .first()
            )

            alternative_results.append(
                {
                    "supplier_id": str(
                        alternative.supplier_id
                    ),
                    "supplier_name": (
                        alternative_supplier.supplier_name
                        if alternative_supplier
                        and hasattr(
                            alternative_supplier,
                            "supplier_name",
                        )
                        else None
                    ),
                    "allocation_pct": round(
                        self._number(
                            alternative.allocation_pct
                        ),
                        2,
                    ),
                    "allocated_capacity_units": round(
                        allocated_capacity,
                        2,
                    ),
                    "spare_capacity_units": round(
                        spare_capacity,
                        2,
                    ),
                    "recoverable_supply_units": round(
                        recoverable,
                        2,
                    ),
                    "lead_time_days": round(
                        self._number(
                            alternative.lead_time_days
                        ),
                        2,
                    ),
                    "criticality": (
                        alternative.criticality
                    ),
                }
            )

        unrecovered_supply = max(
            0.0,
            lost_supply - total_recovery,
        )

        recovery_percentage = (
            (
                total_recovery
                / lost_supply
            )
            * 100.0
            if lost_supply > 0
            else 100.0
        )

        diversity = len(
            alternatives
        )

        criticality = (
            allocation.criticality
            or "medium"
        )

        return {
            "component_id": component_id,
            "component_name": (
                component.component_name
                if component
                else None
            ),
            "plant_id": plant_id,
            "plant_name": (
                plant.plant_name
                if plant
                else None
            ),
            "failed_supplier_id": (
                failed_supplier_id
            ),
            "lost_supply_units": round(
                lost_supply,
                2,
            ),
            "alternative_suppliers": (
                alternative_results
            ),
            "alternative_supplier_count": (
                diversity
            ),
            "recoverable_supply_units": round(
                total_recovery,
                2,
            ),
            "unrecovered_supply_units": round(
                unrecovered_supply,
                2,
            ),
            "recovery_percentage": round(
                recovery_percentage,
                2,
            ),
            "criticality": criticality,
            "resilience_status": (
                self._allocation_status(
                    recovery_percentage,
                    diversity,
                )
            ),
        }

    # ============================================================
    # RESILIENCE SCORE
    # ============================================================

    def _calculate_resilience_score(
        self,
        results: list[dict[str, Any]],
    ) -> float:

        if not results:
            return 0.0

        total_lost = sum(
            self._number(
                item["lost_supply_units"]
            )
            for item in results
        )

        total_recovery = sum(
            self._number(
                item[
                    "recoverable_supply_units"
                ]
            )
            for item in results
        )

        recovery_percentage = (
            (
                total_recovery
                / total_lost
            )
            * 100.0
            if total_lost > 0
            else 100.0
        )

        # Recovery contributes maximum 70 points.
        recovery_score = min(
            70.0,
            recovery_percentage * 0.70,
        )

        # Supplier diversity contributes maximum 20 points.
        diversity_scores: list[float] = []

        for item in results:

            alternative_count = int(
                item.get(
                    "alternative_supplier_count",
                    0,
                )
            )

            if alternative_count >= 3:
                diversity_scores.append(
                    20.0
                )

            elif alternative_count == 2:
                diversity_scores.append(
                    15.0
                )

            elif alternative_count == 1:
                diversity_scores.append(
                    10.0
                )

            else:
                diversity_scores.append(
                    0.0
                )

        diversity_score = (
            sum(diversity_scores)
            / len(diversity_scores)
            if diversity_scores
            else 0.0
        )

        # Criticality contributes a penalty.
        penalties: list[float] = []

        for item in results:

            criticality = str(
                item.get(
                    "criticality",
                    "medium",
                )
            ).lower()

            if criticality == "critical":
                penalties.append(15.0)

            elif criticality == "high":
                penalties.append(10.0)

            elif criticality == "medium":
                penalties.append(5.0)

            else:
                penalties.append(0.0)

        criticality_penalty = (
            sum(penalties)
            / len(penalties)
            if penalties
            else 0.0
        )

        score = (
            recovery_score
            + diversity_score
            - criticality_penalty
        )

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    # ============================================================
    # LEVELS / STATUS
    # ============================================================

    @staticmethod
    def _allocation_status(
        recovery_percentage: float,
        alternative_count: int,
    ) -> str:

        if (
            recovery_percentage >= 80.0
            and alternative_count >= 2
        ):
            return "resilient"

        if (
            recovery_percentage >= 40.0
            or alternative_count >= 1
        ):
            return "moderate"

        if alternative_count == 0:
            return "single_source"

        return "high_risk"

    @classmethod
    def _resilience_level(
        cls,
        score: float,
    ) -> str:

        if score >= cls.RESILIENT_THRESHOLD:
            return "resilient"

        if score >= cls.MODERATE_THRESHOLD:
            return "moderate"

        if score >= cls.HIGH_RISK_THRESHOLD:
            return "high_risk"

        return "critical_risk"

    # ============================================================
    # SUMMARY
    # ============================================================

    def _build_summary(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:

        total_lost = sum(
            self._number(
                item["lost_supply_units"]
            )
            for item in results
        )

        total_recovery = sum(
            self._number(
                item[
                    "recoverable_supply_units"
                ]
            )
            for item in results
        )

        total_unrecovered = max(
            0.0,
            total_lost - total_recovery,
        )

        recovery_percentage = (
            (
                total_recovery
                / total_lost
            )
            * 100.0
            if total_lost > 0
            else 100.0
        )

        return {
            "affected_components": len(
                results
            ),
            "gross_lost_supply_units": round(
                total_lost,
                2,
            ),
            "alternative_recovery_units": round(
                total_recovery,
                2,
            ),
            "unrecovered_supply_units": round(
                total_unrecovered,
                2,
            ),
            "recovery_percentage": round(
                recovery_percentage,
                2,
            ),
            "components_with_alternatives": sum(
                1
                for item in results
                if item[
                    "alternative_supplier_count"
                ]
                > 0
            ),
            "single_source_components": sum(
                1
                for item in results
                if item[
                    "alternative_supplier_count"
                ]
                == 0
            ),
            "critical_components": sum(
                1
                for item in results
                if str(
                    item["criticality"]
                ).lower()
                == "critical"
            ),
            "high_risk_components": sum(
                1
                for item in results
                if item[
                    "resilience_status"
                ]
                == "high_risk"
            ),
        }

    @staticmethod
    def _empty_summary() -> dict[str, Any]:
        return {
            "affected_components": 0,
            "gross_lost_supply_units": 0.0,
            "alternative_recovery_units": 0.0,
            "unrecovered_supply_units": 0.0,
            "recovery_percentage": 0.0,
            "components_with_alternatives": 0,
            "single_source_components": 0,
            "critical_components": 0,
            "high_risk_components": 0,
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _supplier_payload(
        supplier: BusinessSupplier,
    ) -> dict[str, Any]:

        return {
            "supplier_id": str(
                supplier.supplier_id
            ),
            "name": supplier.supplier_name,
            "country": supplier.country,
            "city": supplier.city,
            "location_known": bool(
                supplier.location_known
            ),
        }

    @staticmethod
    def _get_spare_capacity(
        allocation: SupplyAllocation,
    ) -> float:

        value = getattr(
            allocation,
            "spare_capacity_units",
            0.0,
        )

        try:
            return max(
                0.0,
                float(value or 0.0),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _number(value: Any) -> float:

        try:
            return float(
                value or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0


__all__ = [
    "SupplyChainResilienceService",
]