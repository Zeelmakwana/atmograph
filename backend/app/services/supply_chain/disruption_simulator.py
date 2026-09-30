from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.business_supply_chain import (
    BusinessProduct,
    BusinessSupplier,
    Component,
    Demand,
    Dependency,
    Inventory,
    Plant,
    SupplyAllocation,
)
from app.services.supply_chain.route_impact_service import (
    RouteImpactService,
)


class DisruptionSimulator:
    """
    Business supply-chain disruption simulator.

    Supplier failure
        ↓
    Lost supplier allocation
        ↓
    Explicit alternate supplier spare capacity
        ↓
    Alternative recovery
        ↓
    Route disruption
        ↓
    Inventory buffer
        ↓
    Product demand
        ↓
    Net shortage
        ↓
    Production impact
        ↓
    Risk

    Important business rules:

    1. capacity_units is the supplier's normal allocation.
    2. spare_capacity_units is the explicitly declared
       additional capacity available for disruption recovery.
    3. Plant production capacity is NOT treated as supplier
       spare capacity.
    4. Unknown spare capacity is treated as zero, not guessed.
    5. Inventory protects against component shortage.
    6. Normal route transit is not itself a disruption delay.
    """

    def __init__(
        self,
        db: Session,
        user_id: int | None = None,
    ) -> None:
        self.db = db
        self.user_id = user_id
        self.route_service = RouteImpactService(
            db,
            user_id=user_id,
        )

    def _query(self, model):
        query = self.db.query(model)
        if self.user_id is not None:
            query = query.filter(model.user_id == self.user_id)
        return query

    # =========================================================
    # PUBLIC
    # =========================================================

    def simulate_supplier_failure(
        self,
        supplier_id: str,
        disruption_location: str | None = None,
        severity: str | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:

        supplier = (
            self._query(BusinessSupplier)
            .filter(
                BusinessSupplier.supplier_id
                == supplier_id
            )
            .first()
        )

        if supplier is None:
            return {
                "success": False,
                "error": (
                    f"Supplier not found: {supplier_id}"
                ),
            }

        route_impact = (
            self.route_service.analyze_supplier_routes(
                supplier_id=supplier_id,
                disruption_location=(
                    disruption_location
                ),
                severity=severity,
                event_type=event_type,
            )
        )

        allocations = (
            self._query(SupplyAllocation)
            .filter(
                SupplyAllocation.supplier_id
                == supplier_id
            )
            .all()
        )

        if not allocations:
            return {
                "success": True,
                "simulation_type": "supplier_failure",
                "supplier": self._supplier_payload(
                    supplier
                ),
                "scenario": {
                    "disruption_location": (
                        disruption_location
                    ),
                    "severity": severity,
                    "event_type": event_type,
                },
                "route_impact": route_impact,
                "components": [],
                "products": [],
                "plants": [],
                "summary": self._empty_summary(),
            }

        component_results: list[
            dict[str, Any]
        ] = []

        for allocation in allocations:
            component_results.append(
                self._simulate_component(
                    failed_supplier_id=supplier_id,
                    allocation=allocation,
                    route_impact=route_impact,
                )
            )

        products = (
            self._calculate_product_impacts(
                component_results
            )
        )

        plants = (
            self._calculate_plant_impacts(
                component_results,
                products,
            )
        )

        summary = self._build_summary(
            component_results,
            products,
            plants,
        )

        return {
            "success": True,
            "simulation_type": "supplier_failure",
            "supplier": self._supplier_payload(
                supplier
            ),
            "scenario": {
                "disruption_location": (
                    disruption_location
                ),
                "severity": severity,
                "event_type": event_type,
            },
            "route_impact": route_impact,
            "components": component_results,
            "products": products,
            "plants": plants,
            "summary": summary,
        }

    # =========================================================
    # COMPONENT SIMULATION
    # =========================================================

    def _simulate_component(
        self,
        failed_supplier_id: str,
        allocation: SupplyAllocation,
        route_impact: dict[str, Any],
    ) -> dict[str, Any]:

        component = (
            self._query(Component)
            .filter(
                Component.component_id
                == str(
                    allocation.component_id
                )
            )
            .first()
        )

        plant = (
            self._query(Plant)
            .filter(
                Plant.plant_id
                == str(
                    allocation.plant_id
                )
            )
            .first()
        )

        # -----------------------------------------------------
        # Lost supplier allocation
        # -----------------------------------------------------

        lost_supply = self._number(
            allocation.capacity_units
        )

        # -----------------------------------------------------
        # Alternative suppliers
        # -----------------------------------------------------

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

        total_recovery = 0.0
        remaining_loss = lost_supply

        # -----------------------------------------------------
        # Recover lost supply using explicit spare capacity.
        #
        # No plant-capacity inference.
        # No lead-time inference.
        # No guessing.
        # -----------------------------------------------------

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

            alternative_results.append(
                {
                    "supplier_id": (
                        alternative.supplier_id
                    ),
                    "allocation_pct": (
                        self._number(
                            alternative.allocation_pct
                        )
                    ),
                    "allocated_capacity_units": (
                        round(
                            allocated_capacity,
                            2,
                        )
                    ),
                    "spare_capacity_units": (
                        round(
                            spare_capacity,
                            2,
                        )
                    ),
                    "recoverable_supply_units": (
                        round(
                            recoverable,
                            2,
                        )
                    ),
                    "remaining_loss_after_recovery": (
                        round(
                            remaining_loss,
                            2,
                        )
                    ),
                    "lead_time_days": (
                        self._number(
                            alternative.lead_time_days
                        )
                    ),
                    "criticality": (
                        alternative.criticality
                    ),
                }
            )

            if remaining_loss <= 0:
                break

        # -----------------------------------------------------
        # Shortage before inventory
        # -----------------------------------------------------

        gross_shortage = max(
            0.0,
            lost_supply - total_recovery,
        )

        # -----------------------------------------------------
        # Inventory
        # -----------------------------------------------------

        inventory_quantity = (
            self._get_inventory(
                component_id=(
                    allocation.component_id
                )
            )
        )

        # -----------------------------------------------------
        # Demand
        # -----------------------------------------------------

        product_demands = (
            self._get_product_demands(
                component_id=(
                    allocation.component_id
                ),
                plant_id=(
                    allocation.plant_id
                ),
            )
        )

        daily_demand = sum(
            self._number(
                item[
                    "daily_demand_units"
                ]
            )
            * self._number(
                item[
                    "required_quantity"
                ]
            )
            for item in product_demands
        )

        # -----------------------------------------------------
        # Inventory coverage
        # -----------------------------------------------------

        inventory_coverage_days = None

        if daily_demand > 0:
            inventory_coverage_days = (
                inventory_quantity
                / daily_demand
            )

        # -----------------------------------------------------
        # Net shortage after inventory
        # -----------------------------------------------------

        net_shortage = max(
            0.0,
            gross_shortage
            - inventory_quantity,
        )

        # -----------------------------------------------------
        # Shortage delay
        # -----------------------------------------------------

        shortage_delay_days = 0.0

        if daily_demand > 0:
            shortage_delay_days = (
                net_shortage
                / daily_demand
            )

        # -----------------------------------------------------
        # Route disruption
        # -----------------------------------------------------

        route_disruption_delay = (
            self._number(
                route_impact.get(
                    "additional_disruption_delay_days",
                    route_impact.get(
                        "route_disruption_delay_days",
                        0,
                    ),
                )
            )
        )

        effective_route_time = (
            self._number(
                route_impact.get(
                    "effective_route_time_days",
                    0,
                )
            )
        )

        estimated_delay_days = max(
            shortage_delay_days,
            route_disruption_delay,
        )

        # -----------------------------------------------------
        # Production stop
        # -----------------------------------------------------

        production_stop = (
            net_shortage > 0
            and daily_demand > 0
        )

        # -----------------------------------------------------
        # Risk
        # -----------------------------------------------------

        risk_score = (
            self._calculate_risk(
                lost_supply=lost_supply,
                gross_shortage=gross_shortage,
                net_shortage=net_shortage,
                inventory=inventory_quantity,
                inventory_coverage_days=(
                    inventory_coverage_days
                ),
                disruption_delay_days=(
                    route_disruption_delay
                ),
                shortage_delay_days=(
                    shortage_delay_days
                ),
                criticality=(
                    allocation.criticality
                ),
            )
        )

        confidence = self._confidence(
            allocation=allocation,
            alternatives=alternatives,
            daily_demand=daily_demand,
            route_impact=route_impact,
        )

        return {
            "component_id": (
                component.component_id
                if component
                else allocation.component_id
            ),
            "component_name": (
                component.component_name
                if component
                else "Unknown"
            ),
            "plant_id": allocation.plant_id,
            "plant_name": (
                plant.plant_name
                if plant
                else "Unknown"
            ),
            "failed_supplier_id": (
                failed_supplier_id
            ),
            "gross_lost_supply": round(
                lost_supply,
                2,
            ),
            "alternative_suppliers": (
                alternative_results
            ),
            "alternative_recovery": round(
                total_recovery,
                2,
            ),
            "gross_shortage": round(
                gross_shortage,
                2,
            ),
            "inventory_quantity": round(
                inventory_quantity,
                2,
            ),
            "inventory_coverage_days": (
                round(
                    inventory_coverage_days,
                    2,
                )
                if inventory_coverage_days
                is not None
                else None
            ),
            "product_demands": (
                product_demands
            ),
            "daily_demand": round(
                daily_demand,
                2,
            ),
            "net_shortage": round(
                net_shortage,
                2,
            ),
            "shortage_delay_days": round(
                shortage_delay_days,
                2,
            ),
            "route_transit_days": (
                round(
                    self._route_transit_days(
                        route_impact
                    ),
                    2,
                )
            ),
            "route_disruption_delay_days": (
                round(
                    route_disruption_delay,
                    2,
                )
            ),
            "effective_route_time_days": (
                round(
                    effective_route_time,
                    2,
                )
            ),
            "estimated_delay_days": round(
                estimated_delay_days,
                2,
            ),
            "production_stop": (
                production_stop
            ),
            "risk_score": round(
                risk_score,
                2,
            ),
            "risk_level": self._risk_level(
                risk_score
            ),
            "confidence": confidence,
        }

    # =========================================================
    # INVENTORY
    # =========================================================

    def _get_inventory(
        self,
        component_id: str,
    ) -> float:

        rows = (
            self._query(Inventory)
            .all()
        )

        target = self._normalize_id(
            component_id
        )

        return sum(
            self._number(
                row.quantity_units
            )
            for row in rows
            if self._normalize_id(
                row.component_id
            )
            == target
        )

    # =========================================================
    # PRODUCT DEMANDS
    # =========================================================

    def _get_product_demands(
        self,
        component_id: str,
        plant_id: str,
    ) -> list[dict[str, Any]]:

        target_component = (
            self._normalize_id(
                component_id
            )
        )

        target_plant = (
            self._normalize_id(
                plant_id
            )
        )

        dependencies = (
            self._query(
                Dependency
            )
            .all()
        )

        products = (
            self._query(
                BusinessProduct
            )
            .all()
        )

        demands = (
            self._query(
                Demand
            )
            .all()
        )

        products_by_id = {
            self._normalize_id(
                product.product_id
            ): product
            for product in products
        }

        results: list[
            dict[str, Any]
        ] = []

        seen: set[
            tuple[str, str, str]
        ] = set()

        for dependency in dependencies:

            source_type = (
                str(
                    dependency.source_type
                    or ""
                )
                .strip()
                .lower()
            )

            target_type = (
                str(
                    dependency.target_type
                    or ""
                )
                .strip()
                .lower()
            )

            if source_type == "product" and target_type == "component":
                if (
                    self._normalize_id(
                        dependency.target_id
                    )
                    != target_component
                ):
                    continue
                product_id = (
                    self._normalize_id(
                        dependency.source_id
                    )
                )
            elif source_type == "component" and target_type == "product":
                if (
                    self._normalize_id(
                        dependency.source_id
                    )
                    != target_component
                ):
                    continue
                product_id = (
                    self._normalize_id(
                        dependency.target_id
                    )
                )
            else:
                continue

            product_obj = (
                products_by_id.get(
                    product_id
                )
            )

            if product_obj is None:
                continue

            required_quantity = (
                self._dependency_quantity(
                    dependency
                )
            )

            for demand in demands:

                if (
                    self._normalize_id(
                        demand.plant_id
                    )
                    != target_plant
                ):
                    continue

                if (
                    self._normalize_id(
                        demand.product_id
                    )
                    != product_id
                ):
                    continue

                key = (
                    product_id,
                    target_component,
                    target_plant,
                )

                if key in seen:
                    continue

                seen.add(key)

                results.append(
                    {
                        "product_id": (
                            product_obj.product_id
                        ),
                        "product_name": (
                            product_obj.product_name
                        ),
                        "plant_id": (
                            demand.plant_id
                        ),
                        "daily_demand_units": (
                            round(
                                self._number(
                                    demand.daily_demand_units
                                ),
                                2,
                            )
                        ),
                        "required_quantity": (
                            required_quantity
                        ),
                        "dependency_type": (
                            dependency.dependency_type
                        ),
                        "criticality": (
                            dependency.criticality
                        ),
                    }
                )

        return results

    # =========================================================
    # DEPENDENCY QUANTITY
    # =========================================================

    @staticmethod
    def _dependency_quantity(
        dependency: Dependency,
    ) -> float:

        value = getattr(
            dependency,
            "required_quantity",
            None,
        )

        if value is None:
            return 1.0

        try:
            return max(
                0.0,
                float(value),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 1.0

    # =========================================================
    # ALTERNATIVE SPARE CAPACITY
    # =========================================================

    @staticmethod
    def _get_spare_capacity(
        allocation: SupplyAllocation,
    ) -> float:
        """
        Return explicitly declared spare capacity.

        This deliberately does NOT derive spare capacity from:

        - plant capacity
        - lead time
        - allocation percentage
        - demand
        - any guessed value

        If the dataset does not specify spare capacity,
        recovery is zero.
        """

        value = getattr(
            allocation,
            "spare_capacity_units",
            None,
        )

        if value is None:
            return 0.0

        try:
            return max(
                0.0,
                float(value),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    # =========================================================
    # PRODUCT IMPACT
    # =========================================================

    def _calculate_product_impacts(
        self,
        component_results: list[
            dict[str, Any]
        ],
    ) -> list[dict[str, Any]]:

        results: list[
            dict[str, Any]
        ] = []

        components_by_id = {
            self._normalize_id(
                item["component_id"]
            ): item
            for item in component_results
        }

        dependencies = (
            self.db.query(
                Dependency
            )
            .all()
        )

        products = (
            self.db.query(
                BusinessProduct
            )
            .all()
        )

        demands = (
            self.db.query(
                Demand
            )
            .all()
        )

        products_by_id = {
            self._normalize_id(
                product.product_id
            ): product
            for product in products
        }

        seen: set[
            tuple[str, str, str]
        ] = set()

        for dependency in dependencies:

            if (
                str(
                    dependency.source_type
                    or ""
                )
                .strip()
                .lower()
                != "product"
            ):
                continue

            if (
                str(
                    dependency.target_type
                    or ""
                )
                .strip()
                .lower()
                != "component"
            ):
                continue

            component = (
                components_by_id.get(
                    self._normalize_id(
                        dependency.target_id
                    )
                )
            )

            if component is None:
                continue

            product = (
                products_by_id.get(
                    self._normalize_id(
                        dependency.source_id
                    )
                )
            )

            if product is None:
                continue

            plant_id = self._normalize_id(
                component["plant_id"]
            )

            demand_row = next(
                (
                    demand
                    for demand in demands
                    if (
                        self._normalize_id(
                            demand.plant_id
                        )
                        == plant_id
                        and self._normalize_id(
                            demand.product_id
                        )
                        == self._normalize_id(
                            product.product_id
                        )
                    )
                ),
                None,
            )

            if demand_row is None:
                continue

            key = (
                self._normalize_id(
                    product.product_id
                ),
                self._normalize_id(
                    dependency.target_id
                ),
                plant_id,
            )

            if key in seen:
                continue

            seen.add(key)

            required_quantity = (
                self._dependency_quantity(
                    dependency
                )
            )

            component_shortage = (
                self._number(
                    component[
                        "net_shortage"
                    ]
                )
            )

            product_shortage = (
                component_shortage
                / required_quantity
                if required_quantity > 0
                else component_shortage
            )

            daily_demand = (
                self._number(
                    demand_row.daily_demand_units
                )
            )

            shortage_delay = (
                product_shortage
                / daily_demand
                if daily_demand > 0
                else 0.0
            )

            route_delay = (
                self._number(
                    component.get(
                        "route_disruption_delay_days",
                        0,
                    )
                )
            )

            delay = max(
                shortage_delay,
                route_delay,
            )

            exposure_status = (
                "shortage"
                if product_shortage > 0
                else (
                    "route_delayed"
                    if route_delay > 0
                    else "buffered"
                )
            )

            results.append(
                {
                    "product_id": (
                        product.product_id
                    ),
                    "product_name": (
                        product.product_name
                    ),
                    "plant_id": (
                        component["plant_id"]
                    ),
                    "component_id": (
                        component["component_id"]
                    ),
                    "component_name": (
                        component["component_name"]
                    ),
                    "exposure_status": (
                        exposure_status
                    ),
                    "gross_component_exposure": (
                        component[
                            "gross_lost_supply"
                        ]
                    ),
                    "component_shortage": round(
                        component_shortage,
                        2,
                    ),
                    "estimated_product_shortage": round(
                        product_shortage,
                        2,
                    ),
                    "daily_demand_units": round(
                        daily_demand,
                        2,
                    ),
                    "estimated_delay_days": round(
                        delay,
                        2,
                    ),
                    "inventory_protected": (
                        product_shortage <= 0
                    ),
                    "production_stop": (
                        product_shortage > 0
                    ),
                    "risk_score": (
                        component["risk_score"]
                    ),
                    "risk_level": (
                        component["risk_level"]
                    ),
                }
            )

        return results

    # =========================================================
    # PLANT IMPACT
    # =========================================================

    def _calculate_plant_impacts(
        self,
        component_results: list[
            dict[str, Any]
        ],
        product_results: list[
            dict[str, Any]
        ],
    ) -> list[dict[str, Any]]:

        plants: dict[
            str,
            dict[str, Any],
        ] = {}

        for component in component_results:

            plant_id = str(
                component["plant_id"]
            )

            if plant_id not in plants:
                plants[plant_id] = {
                    "plant_id": plant_id,
                    "plant_name": (
                        component[
                            "plant_name"
                        ]
                    ),
                    "affected_components": 0,
                    "affected_products": 0,
                    "max_delay_days": 0.0,
                    "max_risk_score": 0.0,
                    "production_stop": False,
                }

            item = plants[plant_id]

            item[
                "affected_components"
            ] += 1

            item[
                "max_delay_days"
            ] = max(
                item[
                    "max_delay_days"
                ],
                self._number(
                    component[
                        "estimated_delay_days"
                    ]
                ),
            )

            item[
                "max_risk_score"
            ] = max(
                item[
                    "max_risk_score"
                ],
                self._number(
                    component[
                        "risk_score"
                    ]
                ),
            )

            if component[
                "production_stop"
            ]:
                item[
                    "production_stop"
                ] = True

        for product in product_results:

            plant_id = str(
                product.get(
                    "plant_id",
                    "",
                )
            )

            if plant_id not in plants:
                continue

            plants[plant_id][
                "affected_products"
            ] += 1

        for item in plants.values():

            item[
                "max_delay_days"
            ] = round(
                item[
                    "max_delay_days"
                ],
                2,
            )

            item[
                "max_risk_score"
            ] = round(
                item[
                    "max_risk_score"
                ],
                2,
            )

            item["risk_level"] = (
                self._risk_level(
                    item[
                        "max_risk_score"
                    ]
                )
            )

        return list(
            plants.values()
        )

    # =========================================================
    # RISK
    # =========================================================

    @staticmethod
    def _calculate_risk(
        lost_supply: float,
        gross_shortage: float,
        net_shortage: float,
        inventory: float,
        inventory_coverage_days: float | None,
        disruption_delay_days: float,
        shortage_delay_days: float,
        criticality: str | None,
    ) -> float:

        score = 0.0

        if lost_supply > 0:
            score += 20

        if gross_shortage > 0:
            score += 15

        if net_shortage > 0:
            score += 30

        if disruption_delay_days > 0:
            score += min(
                20,
                disruption_delay_days * 2.5,
            )

        if shortage_delay_days > 0:
            score += min(
                15,
                shortage_delay_days * 3,
            )

        if inventory <= 0:
            score += 10

        elif inventory_coverage_days is not None:

            if inventory_coverage_days < 3:
                score += 8

            elif inventory_coverage_days < 7:
                score += 5

            elif inventory_coverage_days < 14:
                score += 2

            else:
                score -= 10

        criticality_value = str(
            criticality or ""
        ).strip().lower()

        if criticality_value == "critical":
            score += 10

        elif criticality_value == "high":
            score += 7

        elif criticality_value == "medium":
            score += 4

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    # =========================================================
    # CONFIDENCE
    # =========================================================

    @staticmethod
    def _confidence(
        allocation: SupplyAllocation,
        alternatives: Any,
        daily_demand: float,
        route_impact: dict[str, Any],
    ) -> float:

        known = 0
        total = 4

        if (
            allocation.capacity_units
            is not None
        ):
            known += 1

        if alternatives is not None:
            known += 1

        if daily_demand > 0:
            known += 1

        if route_impact.get(
            "routes_known",
            False,
        ):
            known += 1

        return round(
            known / total,
            2,
        )

    # =========================================================
    # ROUTE HELPERS
    # =========================================================

    @staticmethod
    def _route_transit_days(
        route_impact: dict[str, Any],
    ) -> float:

        routes = route_impact.get(
            "routes",
            [],
        )

        return max(
            (
                DisruptionSimulator._number(
                    route.get(
                        "transit_days",
                        route.get(
                            "normal_transit_days",
                            0,
                        ),
                    )
                )
                for route in routes
                if route.get(
                    "disrupted",
                    False,
                )
            ),
            default=0.0,
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    @staticmethod
    def _build_summary(
        components: list[
            dict[str, Any]
        ],
        products: list[
            dict[str, Any]
        ],
        plants: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:

        return {
            "affected_components": len(
                components
            ),
            "affected_products": len(
                products
            ),
            "affected_plants": len(
                plants
            ),
            "gross_lost_supply": round(
                sum(
                    DisruptionSimulator._number(
                        item.get(
                            "gross_lost_supply",
                            0,
                        )
                    )
                    for item in components
                ),
                2,
            ),
            "alternative_recovery": round(
                sum(
                    DisruptionSimulator._number(
                        item.get(
                            "alternative_recovery",
                            0,
                        )
                    )
                    for item in components
                ),
                2,
            ),
            "gross_shortage": round(
                sum(
                    DisruptionSimulator._number(
                        item.get(
                            "gross_shortage",
                            0,
                        )
                    )
                    for item in components
                ),
                2,
            ),
            "net_shortage": round(
                sum(
                    DisruptionSimulator._number(
                        item.get(
                            "net_shortage",
                            0,
                        )
                    )
                    for item in components
                ),
                2,
            ),
            "max_delay_days": round(
                max(
                    (
                        DisruptionSimulator._number(
                            item.get(
                                "estimated_delay_days",
                                0,
                            )
                        )
                        for item in components
                    ),
                    default=0.0,
                ),
                2,
            ),
            "max_route_disruption_delay_days": round(
                max(
                    (
                        DisruptionSimulator._number(
                            item.get(
                                "route_disruption_delay_days",
                                0,
                            )
                        )
                        for item in components
                    ),
                    default=0.0,
                ),
                2,
            ),
            "max_risk_score": round(
                max(
                    (
                        DisruptionSimulator._number(
                            item.get(
                                "risk_score",
                                0,
                            )
                        )
                        for item in components
                    ),
                    default=0.0,
                ),
                2,
            ),
            "production_stop": any(
                item.get(
                    "production_stop",
                    False,
                )
                for item in components
            ),
            "products_buffered": sum(
                1
                for item in products
                if item.get(
                    "exposure_status"
                )
                == "buffered"
            ),
            "products_route_delayed": sum(
                1
                for item in products
                if item.get(
                    "exposure_status"
                )
                == "route_delayed"
            ),
            "products_with_shortage": sum(
                1
                for item in products
                if item.get(
                    "exposure_status"
                )
                == "shortage"
            ),
        }

    # =========================================================
    # EMPTY SUMMARY
    # =========================================================

    @staticmethod
    def _empty_summary() -> dict[str, Any]:

        return {
            "affected_components": 0,
            "affected_products": 0,
            "affected_plants": 0,
            "gross_lost_supply": 0,
            "alternative_recovery": 0,
            "gross_shortage": 0,
            "net_shortage": 0,
            "max_delay_days": 0,
            "max_route_disruption_delay_days": 0,
            "max_risk_score": 0,
            "production_stop": False,
            "products_buffered": 0,
            "products_route_delayed": 0,
            "products_with_shortage": 0,
        }

    # =========================================================
    # SUPPLIER PAYLOAD
    # =========================================================

    @staticmethod
    def _supplier_payload(
        supplier: BusinessSupplier,
    ) -> dict[str, Any]:

        return {
            "supplier_id": (
                supplier.supplier_id
            ),
            "name": (
                supplier.supplier_name
            ),
            "country": supplier.country,
            "city": supplier.city,
        }

    # =========================================================
    # NORMALIZE ID
    # =========================================================

    @staticmethod
    def _normalize_id(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        return str(
            value
        ).strip().lower()

    # =========================================================
    # NUMBER
    # =========================================================

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:
            return max(
                0.0,
                float(value or 0),
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    # =========================================================
    # RISK LEVEL
    # =========================================================

    @staticmethod
    def _risk_level(
        score: float,
    ) -> str:

        if score >= 75:
            return "critical"

        if score >= 50:
            return "high"

        if score >= 25:
            return "medium"

        return "low"


__all__ = [
    "DisruptionSimulator",
]