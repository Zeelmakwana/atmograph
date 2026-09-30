from __future__ import annotations

from typing import Any


class BusinessImpactService:
    """
    Canonical business-impact normalizer for AtmoGraph.

    Supports both:

    1. Current simulator format:

        simulations[]
            -> {
                supplier,
                simulation: {
                    components,
                    products,
                    plants,
                    summary,
                    route_impact
                }
            }

    2. Simplified / normalized format:

        simulations[]
            -> {
                components,
                products,
                plants,
                summary,
                route_impact
            }

    The service never invents supply-chain facts.
    """

    def build(
        self,
        business_impact: dict[str, Any] | None,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        event_location: str | None = None,
    ) -> dict[str, Any]:

        raw = (
            business_impact
            if isinstance(
                business_impact,
                dict,
            )
            else {}
        )

        raw_simulations = raw.get(
            "simulations",
            [],
        )

        if not isinstance(
            raw_simulations,
            list,
        ):
            raw_simulations = []

        simulations = (
            self._normalize_simulations(
                raw_simulations
            )
        )

        summary = self._aggregate(
            raw=raw,
            simulations=simulations,
        )

        suppliers = (
            self._normalize_suppliers(
                raw.get(
                    "suppliers",
                    [],
                )
            )
        )

        recommendations = (
            self._recommendations(
                summary=summary,
                event_type=event_type,
                severity=severity,
                event_location=event_location,
            )
        )

        return {
            "success": bool(
                raw.get(
                    "success",
                    bool(simulations),
                )
            ),

            "status": raw.get(
                "status",
                (
                    "simulated"
                    if simulations
                    else "unknown"
                ),
            ),

            "message": raw.get(
                "message",
                "",
            ),

            "event_context": (
                raw.get(
                    "event_context",
                    {},
                )
                if isinstance(
                    raw.get(
                        "event_context",
                        {},
                    ),
                    dict,
                )
                else {}
            ),

            "suppliers": suppliers,

            "simulations": simulations,

            "summary": summary,

            "recommendations": recommendations,
        }

    # =========================================================
    # SIMULATION NORMALIZATION
    # =========================================================

    def _normalize_simulations(
        self,
        simulations: list[Any],
    ) -> list[dict[str, Any]]:

        results: list[
            dict[str, Any]
        ] = []

        for group in simulations:

            if not isinstance(
                group,
                dict,
            ):
                continue

            # -------------------------------------------------
            # Current nested simulator structure.
            # -------------------------------------------------

            if isinstance(
                group.get(
                    "simulation"
                ),
                dict,
            ):
                simulation = group[
                    "simulation"
                ]

                supplier = group.get(
                    "supplier",
                    {},
                )

            # -------------------------------------------------
            # Already-normalized / flat structure.
            # -------------------------------------------------

            else:
                simulation = group

                supplier = group.get(
                    "supplier",
                    {},
                )

            if not isinstance(
                simulation,
                dict,
            ):
                simulation = {}

            if not isinstance(
                supplier,
                dict,
            ):
                supplier = {}

            components = simulation.get(
                "components",
                [],
            )

            products = simulation.get(
                "products",
                [],
            )

            plants = simulation.get(
                "plants",
                [],
            )

            summary = simulation.get(
                "summary",
                {},
            )

            route_impact = simulation.get(
                "route_impact",
                {},
            )

            results.append(
                {
                    "success": bool(
                        simulation.get(
                            "success",
                            False,
                        )
                    ),

                    "supplier": supplier,

                    "components": (
                        components
                        if isinstance(
                            components,
                            list,
                        )
                        else []
                    ),

                    "products": (
                        products
                        if isinstance(
                            products,
                            list,
                        )
                        else []
                    ),

                    "plants": (
                        plants
                        if isinstance(
                            plants,
                            list,
                        )
                        else []
                    ),

                    "summary": (
                        summary
                        if isinstance(
                            summary,
                            dict,
                        )
                        else {}
                    ),

                    "route_impact": (
                        route_impact
                        if isinstance(
                            route_impact,
                            dict,
                        )
                        else {}
                    ),
                }
            )

        return results

    # =========================================================
    # AGGREGATION
    # =========================================================

    def _aggregate(
        self,
        *,
        raw: dict[str, Any],
        simulations: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # If caller already supplied a meaningful summary,
        # preserve it.
        #
        # This supports the contract test and future services.
        # -----------------------------------------------------

        supplied_summary = raw.get(
            "summary"
        )

        if not isinstance(
            supplied_summary,
            dict,
        ):
            supplied_summary = {}

        # -----------------------------------------------------
        # Start aggregate.
        # -----------------------------------------------------

        summary = {
            "affected_components": 0,
            "affected_products": 0,
            "affected_plants": 0,

            "gross_lost_supply": 0.0,
            "alternative_recovery": 0.0,
            "gross_shortage": 0.0,
            "net_shortage": 0.0,

            "normal_transit_days": 0.0,
            "additional_disruption_delay_days": 0.0,
            "effective_route_time_days": 0.0,

            "max_delay_days": 0.0,
            "max_route_disruption_delay_days": 0.0,

            "max_risk_score": 0.0,

            "production_stop": False,

            "products_buffered": 0,
            "products_route_delayed": 0,
            "products_with_shortage": 0,
        }

        # -----------------------------------------------------
        # Preserve explicitly supplied top-level summary.
        # -----------------------------------------------------

        for key in summary:

            if key not in supplied_summary:
                continue

            value = supplied_summary[
                key
            ]

            if key == "production_stop":
                summary[key] = bool(
                    value
                )

            elif key in {
                "affected_components",
                "affected_products",
                "affected_plants",
                "products_buffered",
                "products_route_delayed",
                "products_with_shortage",
            }:
                summary[key] = self._int(
                    value
                )

            else:
                summary[key] = self._number(
                    value
                )

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # If the supplied summary is complete, do not double
        # count the simulation values.
        # -----------------------------------------------------

        has_supplied_business_summary = any(
            key in supplied_summary
            for key in (
                "affected_components",
                "affected_products",
                "affected_plants",
                "gross_lost_supply",
                "alternative_recovery",
                "gross_shortage",
                "net_shortage",
                "max_delay_days",
                "max_route_disruption_delay_days",
                "max_risk_score",
            )
        )

        if not has_supplied_business_summary:

            self._aggregate_simulations(
                summary=summary,
                simulations=simulations,
            )

        else:
            # Even when a business summary exists,
            # route metrics may only exist inside simulations.
            self._aggregate_missing_route_metrics(
                summary=summary,
                simulations=simulations,
            )

        # -----------------------------------------------------
        # Counts from actual detail arrays.
        # -----------------------------------------------------

        if not has_supplied_business_summary:

            component_ids: set[str] = set()
            product_keys: set[str] = set()
            plant_ids: set[str] = set()

            for simulation in simulations:

                for component in simulation.get(
                    "components",
                    [],
                ):

                    if not isinstance(
                        component,
                        dict,
                    ):
                        continue

                    component_id = str(
                        component.get(
                            "component_id",
                            "",
                        )
                    ).strip()

                    if component_id:
                        component_ids.add(
                            component_id
                        )

                for product in simulation.get(
                    "products",
                    [],
                ):

                    if not isinstance(
                        product,
                        dict,
                    ):
                        continue

                    product_id = str(
                        product.get(
                            "product_id",
                            "",
                        )
                    ).strip()

                    plant_id = str(
                        product.get(
                            "plant_id",
                            "",
                        )
                    ).strip()

                    component_id = str(
                        product.get(
                            "component_id",
                            "",
                        )
                    ).strip()

                    if product_id:
                        product_keys.add(
                            (
                                f"{product_id}:"
                                f"{plant_id}:"
                                f"{component_id}"
                            )
                        )

                for plant in simulation.get(
                    "plants",
                    [],
                ):

                    if not isinstance(
                        plant,
                        dict,
                    ):
                        continue

                    plant_id = str(
                        plant.get(
                            "plant_id",
                            "",
                        )
                    ).strip()

                    if plant_id:
                        plant_ids.add(
                            plant_id
                        )

            if component_ids:
                summary[
                    "affected_components"
                ] = len(
                    component_ids
                )

            if product_keys:
                summary[
                    "affected_products"
                ] = len(
                    product_keys
                )

            if plant_ids:
                summary[
                    "affected_plants"
                ] = len(
                    plant_ids
                )

        # -----------------------------------------------------
        # Derive gross shortage only if missing.
        # -----------------------------------------------------

        if (
            summary[
                "gross_shortage"
            ] <= 0
            and summary[
                "gross_lost_supply"
            ] > 0
        ):

            summary[
                "gross_shortage"
            ] = max(
                0.0,
                summary[
                    "gross_lost_supply"
                ]
                - summary[
                    "alternative_recovery"
                ],
            )

        return self._finalize_summary(
            summary
        )

    # =========================================================
    # SIMULATION AGGREGATION
    # =========================================================

    def _aggregate_simulations(
        self,
        *,
        summary: dict[str, Any],
        simulations: list[
            dict[str, Any]
        ],
    ) -> None:

        for simulation in simulations:

            if not simulation.get(
                "success",
                False,
            ):
                continue

            simulation_summary = (
                simulation.get(
                    "summary",
                    {},
                )
            )

            # -------------------------------------------------
            # Supply
            # -------------------------------------------------

            summary[
                "gross_lost_supply"
            ] += self._number(
                simulation_summary.get(
                    "gross_lost_supply",
                    0,
                )
            )

            summary[
                "alternative_recovery"
            ] += self._number(
                simulation_summary.get(
                    "alternative_recovery",
                    0,
                )
            )

            summary[
                "gross_shortage"
            ] += self._number(
                simulation_summary.get(
                    "gross_shortage",
                    0,
                )
            )

            summary[
                "net_shortage"
            ] += self._number(
                simulation_summary.get(
                    "net_shortage",
                    0,
                )
            )

            # -------------------------------------------------
            # Risk
            # -------------------------------------------------

            summary[
                "max_risk_score"
            ] = max(
                summary[
                    "max_risk_score"
                ],
                self._number(
                    simulation_summary.get(
                        "max_risk_score",
                        0,
                    )
                ),
            )

            # -------------------------------------------------
            # Production
            # -------------------------------------------------

            if simulation_summary.get(
                "production_stop",
                False,
            ):
                summary[
                    "production_stop"
                ] = True

            # -------------------------------------------------
            # Product counts
            # -------------------------------------------------

            summary[
                "products_buffered"
            ] += self._int(
                simulation_summary.get(
                    "products_buffered",
                    0,
                )
            )

            summary[
                "products_route_delayed"
            ] += self._int(
                simulation_summary.get(
                    "products_route_delayed",
                    0,
                )
            )

            summary[
                "products_with_shortage"
            ] += self._int(
                simulation_summary.get(
                    "products_with_shortage",
                    0,
                )
            )

            # -------------------------------------------------
            # Delay
            # -------------------------------------------------

            summary[
                "max_delay_days"
            ] = max(
                summary[
                    "max_delay_days"
                ],
                self._number(
                    simulation_summary.get(
                        "max_delay_days",
                        0,
                    )
                ),
            )

    # =========================================================
    # ROUTE METRICS
    # =========================================================

    def _aggregate_missing_route_metrics(
        self,
        *,
        summary: dict[str, Any],
        simulations: list[
            dict[str, Any]
        ],
    ) -> None:

        for simulation in simulations:

            route = simulation.get(
                "route_impact",
                {},
            )

            if not isinstance(
                route,
                dict,
            ):
                continue

            summary[
                "normal_transit_days"
            ] = max(
                summary[
                    "normal_transit_days"
                ],
                self._number(
                    route.get(
                        "normal_transit_days",
                        0,
                    )
                ),
            )

            summary[
                "additional_disruption_delay_days"
            ] = max(
                summary[
                    "additional_disruption_delay_days"
                ],
                self._number(
                    route.get(
                        "additional_disruption_delay_days",
                        route.get(
                            "route_disruption_delay_days",
                            0,
                        ),
                    )
                ),
            )

            summary[
                "effective_route_time_days"
            ] = max(
                summary[
                    "effective_route_time_days"
                ],
                self._number(
                    route.get(
                        "effective_route_time_days",
                        0,
                    )
                ),
            )

            summary[
                "max_route_disruption_delay_days"
            ] = max(
                summary[
                    "max_route_disruption_delay_days"
                ],
                self._number(
                    route.get(
                        "additional_disruption_delay_days",
                        route.get(
                            "route_disruption_delay_days",
                            0,
                        ),
                    )
                ),
            )

    # =========================================================
    # FINALIZE
    # =========================================================

    def _finalize_summary(
        self,
        summary: dict[str, Any],
    ) -> dict[str, Any]:

        integer_fields = {
            "affected_components",
            "affected_products",
            "affected_plants",
            "products_buffered",
            "products_route_delayed",
            "products_with_shortage",
        }

        numeric_fields = {
            "gross_lost_supply",
            "alternative_recovery",
            "gross_shortage",
            "net_shortage",
            "normal_transit_days",
            "additional_disruption_delay_days",
            "effective_route_time_days",
            "max_delay_days",
            "max_route_disruption_delay_days",
            "max_risk_score",
        }

        for field in integer_fields:
            summary[field] = self._int(
                summary.get(
                    field,
                    0,
                )
            )

        for field in numeric_fields:
            summary[field] = round(
                self._number(
                    summary.get(
                        field,
                        0,
                    )
                ),
                2,
            )

        summary[
            "production_stop"
        ] = bool(
            summary.get(
                "production_stop",
                False,
            )
        )

        return summary

    # =========================================================
    # SUPPLIERS
    # =========================================================

    def _normalize_suppliers(
        self,
        suppliers: Any,
    ) -> list[dict[str, Any]]:

        if not isinstance(
            suppliers,
            list,
        ):
            return []

        result = []

        for supplier in suppliers:

            if not isinstance(
                supplier,
                dict,
            ):
                continue

            item = dict(
                supplier
            )

            item.setdefault(
                "supplier_id",
                item.get(
                    "id",
                    "",
                ),
            )

            item.setdefault(
                "name",
                item.get(
                    "supplier_name",
                    "",
                ),
            )

            item.setdefault(
                "country",
                None,
            )

            item.setdefault(
                "city",
                None,
            )

            item.setdefault(
                "match_score",
                0,
            )

            item.setdefault(
                "match_reasons",
                [],
            )

            item.setdefault(
                "directly_affected",
                True,
            )

            result.append(
                item
            )

        return result

    # =========================================================
    # RECOMMENDATIONS
    # =========================================================

    def _recommendations(
        self,
        *,
        summary: dict[str, Any],
        event_type: str | None,
        severity: str | None,
        event_location: str | None,
    ) -> list[dict[str, str]]:

        recommendations = []

        net_shortage = self._number(
            summary.get(
                "net_shortage",
                0,
            )
        )

        gross_shortage = self._number(
            summary.get(
                "gross_shortage",
                0,
            )
        )

        recovery = self._number(
            summary.get(
                "alternative_recovery",
                0,
            )
        )

        route_delay = self._number(
            summary.get(
                "additional_disruption_delay_days",
                0,
            )
        )

        risk = self._number(
            summary.get(
                "max_risk_score",
                0,
            )
        )

        production_stop = bool(
            summary.get(
                "production_stop",
                False,
            )
        )

        if production_stop:

            recommendations.append(
                {
                    "priority": "critical",
                    "action": (
                        "Protect affected production "
                        "and activate confirmed alternate "
                        "supply options."
                    ),
                    "reason": (
                        "The simulation indicates "
                        "a production-stop condition."
                    ),
                    "source": "simulation",
                }
            )

        if net_shortage > 0:

            recommendations.append(
                {
                    "priority": "critical",
                    "action": (
                        "Escalate the uncovered supply "
                        "shortage for procurement and "
                        "operations planning."
                    ),
                    "reason": (
                        f"{net_shortage:.2f} units remain "
                        "uncovered after inventory and "
                        "alternate recovery."
                    ),
                    "source": "inventory_simulation",
                }
            )

        elif gross_shortage > 0:

            recommendations.append(
                {
                    "priority": "high",
                    "action": (
                        "Review inventory coverage and "
                        "confirmed alternate capacity."
                    ),
                    "reason": (
                        f"{gross_shortage:.2f} units of "
                        "gross shortage remain after "
                        "alternate recovery."
                    ),
                    "source": "simulation",
                }
            )

        if recovery > 0:

            recommendations.append(
                {
                    "priority": "high",
                    "action": (
                        "Evaluate recovered alternate "
                        "supplier capacity for allocation."
                    ),
                    "reason": (
                        f"{recovery:.2f} units of explicit "
                        "alternate capacity are available."
                    ),
                    "source": "alternate_capacity",
                }
            )

        if route_delay > 0:

            suffix = (
                f" near {event_location}"
                if event_location
                else ""
            )

            recommendations.append(
                {
                    "priority": "high",
                    "action": (
                        "Review affected logistics routes "
                        "and shipment schedules."
                    ),
                    "reason": (
                        f"Event adds "
                        f"{route_delay:.2f} days of route "
                        f"disruption{suffix}."
                    ),
                    "source": "route_analysis",
                }
            )

        if risk >= 75:

            recommendations.append(
                {
                    "priority": "critical",
                    "action": (
                        "Escalate the event to supply-chain "
                        "risk management."
                    ),
                    "reason": (
                        f"Maximum modeled business risk "
                        f"is {risk:.2f}/100."
                    ),
                    "source": "risk_engine",
                }
            )

        elif risk >= 50:

            recommendations.append(
                {
                    "priority": "high",
                    "action": (
                        "Increase monitoring of the "
                        "affected supply-chain segment."
                    ),
                    "reason": (
                        f"Maximum modeled business risk "
                        f"is {risk:.2f}/100."
                    ),
                    "source": "risk_engine",
                }
            )

        if not recommendations:

            recommendations.append(
                {
                    "priority": "normal",
                    "action": (
                        "Continue monitoring the event."
                    ),
                    "reason": (
                        "No quantified shortage, delay, "
                        "or production-stop condition "
                        "was identified."
                    ),
                    "source": "simulation",
                }
            )

        return recommendations

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:
            return float(
                value or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _int(
        value: Any,
    ) -> int:

        try:
            return int(
                float(
                    value or 0
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0


__all__ = [
    "BusinessImpactService",
]