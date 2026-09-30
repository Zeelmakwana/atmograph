from __future__ import annotations

from typing import Any

from app.services.operational_intelligence_service import OperationalIntelligenceService

from app.schemas.intelligence import (
    IntelligenceBusinessImpact,
    IntelligenceEvent,
    IntelligencePrediction,
    IntelligenceResilience,
    IntelligenceRisk,
    IntelligenceRouteImpact,
    IntelligenceSupplierExposure,
    UnifiedIntelligence,
)


class UnifiedIntelligenceService:
    """
    Convert the existing AtmoGraph pipeline response into one
    stable, frontend-friendly intelligence contract.

    Architecture:

        Existing Pipeline
              |
              v
        Raw intelligence
              |
              v
        Normalization
              |
              v
        UnifiedIntelligence

    This service does NOT replace:
        - NLP
        - graph construction
        - simulation
        - resilience analysis
        - GNN
        - hybrid prediction

    It creates one stable contract over those systems.

    Important contract rules:

    1. Business simulation is authoritative for BUSINESS IMPACT.
    2. ML/GNN/hybrid prediction remains a separate predictive signal.
    3. Unknown information must remain UNKNOWN.
    4. Legacy pipeline fields are preserved by the API layer.
    """

    VERSION = "1.0"

    # ========================================================
    # PUBLIC
    # ========================================================

    @classmethod
    def build(
        cls,
        raw: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build canonical intelligence response.

        The original raw pipeline response is NOT modified here.
        The API compatibility layer preserves it separately.
        """

        if not isinstance(raw, dict):
            raw = {}

        event = cls._build_event(raw)
        supplier_exposure = cls._build_supplier_exposure(raw)
        business_impact = cls._build_business_impact(raw)
        route_impact = cls._build_route_impact(raw)
        resilience = cls._build_resilience(raw)
        risk = cls._build_risk(raw)
        prediction = cls._build_prediction(raw)
        recommendations = cls._build_recommendations(raw)

        intelligence = UnifiedIntelligence(
            version=cls.VERSION,
            event=event,
            supplier_exposure=supplier_exposure,
            business_impact=business_impact,
            route_impact=route_impact,
            resilience=resilience,
            risk=risk,
            prediction=prediction,
            recommendations=recommendations,
        )

        result = intelligence.model_dump()

        # Deterministic operational timeline/status layer.
        # Business simulation remains authoritative; ML/GNN is not allowed to override it.
        operational = OperationalIntelligenceService.build(raw)
        result.update(operational)

        # ----------------------------------------------------
        # Compatibility / semantic aliases
        # ----------------------------------------------------

        result["event_understanding"] = result["event"]

        # ----------------------------------------------------
        # Preserve the business simulation's maximum route
        # disruption delay inside business_impact.
        #
        # IMPORTANT:
        #
        # Some pipeline versions store this value here:
        #
        # business_supply_chain
        #   -> simulation
        #      -> summary
        #         -> max_route_disruption_delay_days
        #
        # It is NOT necessarily present in route_impact.
        # Therefore we must read the original raw business
        # simulation summary directly.
        # ----------------------------------------------------

        business_impact = result.get(
            "business_impact",
            {},
        )

        business = cls._dict(
            raw.get(
                "business_supply_chain"
            )
        )

        simulation_container = cls._dict(
            business.get(
                "simulation"
            )
        )

        top_summary = cls._dict(
            business.get(
                "summary"
            )
        )

        simulation_summary = cls._dict(
            simulation_container.get(
                "summary"
            )
        )

        fallback = cls._aggregate_simulations(
            cls._get_simulations(
                business
            )
        )

        max_route_disruption_delay = cls._first_present(
            top_summary.get(
                "max_route_disruption_delay_days"
            ),
            simulation_summary.get(
                "max_route_disruption_delay_days"
            ),
            fallback.get(
                "max_route_disruption_delay_days"
            ),
            result.get(
                "route_impact",
                {},
            ).get(
                "additional_disruption_delay_days"
            ),
            0,
        )

        if isinstance(
            business_impact,
            dict,
        ):

            business_impact[
                "max_route_disruption_delay_days"
            ] = cls._number(
                max_route_disruption_delay
            )

        return result

    # ========================================================
    # EVENT
    # ========================================================

    @classmethod
    def _build_event(
        cls,
        raw: dict[str, Any],
    ) -> IntelligenceEvent:

        event = cls._dict(
            raw.get("event")
        )

        nlp = cls._dict(
            raw.get("nlp")
        )

        confidence = cls._first_number_or_none(
            nlp.get("confidence"),
            nlp.get("event_confidence"),
            event.get("confidence"),
        )

        location = cls._string_or_none(
            event.get("location")
        )

        # If the event itself has no location, use the first
        # NLP location only as a fallback.
        if location is None:

            locations = nlp.get(
                "locations",
                [],
            )

            if isinstance(
                locations,
                list,
            ) and locations:

                location = cls._string_or_none(
                    locations[0]
                )

        return IntelligenceEvent(
            event_id=cls._int_or_none(
                event.get(
                    "event_id",
                    event.get("id"),
                )
            ),
            title=str(
                event.get(
                    "title",
                    "",
                )
                or ""
            ),
            description=str(
                event.get(
                    "description",
                    "",
                )
                or ""
            ),
            source=str(
                event.get(
                    "source",
                    "",
                )
                or ""
            ),
            event_type=str(
                event.get(
                    "event_type",
                    nlp.get(
                        "event_type",
                        "unknown",
                    ),
                )
                or "unknown"
            ),
            location=location,
            severity=str(
                event.get(
                    "severity",
                    nlp.get(
                        "severity",
                        "unknown",
                    ),
                )
                or "unknown"
            ),
            status=str(
                event.get(
                    "status",
                    "active",
                )
                or "active"
            ),
            confidence=confidence,
        )

    # ========================================================
    # SUPPLIER EXPOSURE
    # ========================================================

    @classmethod
    def _build_supplier_exposure(
        cls,
        raw: dict[str, Any],
    ) -> IntelligenceSupplierExposure:

        business = cls._dict(
            raw.get(
                "business_supply_chain"
            )
        )

        matched = business.get(
            "matched_suppliers",
            [],
        )

        if not isinstance(
            matched,
            list,
        ):
            matched = []

        affected: list[dict[str, Any]] = []

        simulations = cls._get_simulations(
            business
        )

        for item in simulations:

            simulation = cls._get_simulation(
                item
            )

            supplier = cls._dict(
                item.get(
                    "supplier"
                )
            )

            if not supplier:
                supplier = cls._dict(
                    simulation.get(
                        "supplier"
                    )
                )

            if supplier:
                affected.append(
                    supplier
                )

        affected = cls._dedupe_entities(
            affected
        )

        return IntelligenceSupplierExposure(
            matched_count=len(matched),
            affected_count=len(affected),
            matched_suppliers=matched,
            affected_suppliers=affected,
        )

    # ========================================================
    # BUSINESS IMPACT
    # ========================================================

    @classmethod
    def _build_business_impact(
        cls,
        raw: dict[str, Any],
    ) -> IntelligenceBusinessImpact:

        business = cls._dict(
            raw.get(
                "business_supply_chain"
            )
        )

        simulation_container = cls._dict(
            business.get(
                "simulation"
            )
        )

        # Existing pipeline may expose the canonical summary
        # at business.summary.
        summary = cls._dict(
            business.get(
                "summary"
            )
        )

        # Some pipeline versions expose it under the simulation
        # container.
        if not summary:
            summary = cls._dict(
                simulation_container.get(
                    "summary"
                )
            )

        if not summary:
            summary = cls._dict(
                raw.get(
                    "business_summary"
                )
            )

        simulations = cls._get_simulations(
            business
        )

        fallback = cls._aggregate_simulations(
            simulations
        )

        return IntelligenceBusinessImpact(
            affected_components=cls._int(
                cls._first_present(
                    summary.get(
                        "affected_components"
                    ),
                    fallback[
                        "affected_components"
                    ],
                )
            ),
            affected_products=cls._int(
                cls._first_present(
                    summary.get(
                        "affected_products"
                    ),
                    fallback[
                        "affected_products"
                    ],
                )
            ),
            affected_plants=cls._int(
                cls._first_present(
                    summary.get(
                        "affected_plants"
                    ),
                    fallback[
                        "affected_plants"
                    ],
                )
            ),
            gross_lost_supply=cls._number(
                cls._first_present(
                    summary.get(
                        "gross_lost_supply"
                    ),
                    fallback[
                        "gross_lost_supply"
                    ],
                )
            ),
            alternative_recovery=cls._number(
                cls._first_present(
                    summary.get(
                        "alternative_recovery"
                    ),
                    fallback[
                        "alternative_recovery"
                    ],
                )
            ),
            gross_shortage=cls._number(
                cls._first_present(
                    summary.get(
                        "gross_shortage"
                    ),
                    fallback[
                        "gross_shortage"
                    ],
                )
            ),
            net_shortage=cls._number(
                cls._first_present(
                    summary.get(
                        "net_shortage"
                    ),
                    fallback[
                        "net_shortage"
                    ],
                )
            ),
            products_buffered=cls._int(
                cls._first_present(
                    summary.get(
                        "products_buffered"
                    ),
                    fallback[
                        "products_buffered"
                    ],
                )
            ),
            products_route_delayed=cls._int(
                cls._first_present(
                    summary.get(
                        "products_route_delayed"
                    ),
                    fallback[
                        "products_route_delayed"
                    ],
                )
            ),
            products_with_shortage=cls._int(
                cls._first_present(
                    summary.get(
                        "products_with_shortage"
                    ),
                    fallback[
                        "products_with_shortage"
                    ],
                )
            ),
            production_stop=bool(
                cls._first_present(
                    summary.get(
                        "production_stop"
                    ),
                    fallback[
                        "production_stop"
                    ],
                    False,
                )
            ),
            max_delay_days=cls._number(
                cls._first_present(
                    summary.get(
                        "max_delay_days"
                    ),
                    fallback[
                        "max_delay_days"
                    ],
                )
            ),
            max_risk_score=cls._number(
                cls._first_present(
                    summary.get(
                        "max_risk_score"
                    ),
                    summary.get(
                        "max_risk"
                    ),
                    fallback[
                        "max_risk_score"
                    ],
                )
            ),
        )

    # ========================================================
    # ROUTE IMPACT
    # ========================================================

    @classmethod
    def _build_route_impact(
        cls,
        raw: dict[str, Any],
    ) -> IntelligenceRouteImpact:

        business = cls._dict(
            raw.get(
                "business_supply_chain"
            )
        )

        simulations = cls._get_simulations(
            business
        )

        route_objects: list[dict[str, Any]] = []

        for item in simulations:

            simulation = cls._get_simulation(
                item
            )

            route = cls._dict(
                simulation.get(
                    "route_impact"
                )
            )

            if route:
                route_objects.append(
                    route
                )

        return cls._aggregate_routes(
            route_objects
        )

    @classmethod
    def _aggregate_routes(
        cls,
        routes: list[dict[str, Any]],
    ) -> IntelligenceRouteImpact:

        if not routes:
            return IntelligenceRouteImpact()

        normal = 0.0
        additional = 0.0
        effective = 0.0

        route_delay = 0.0
        effective_delay = 0.0

        analyzed = 0
        disrupted = 0

        known = False
        location_match = False

        for route in routes:

            known = (
                known
                or bool(
                    route.get(
                        "routes_known",
                        False,
                    )
                )
            )

            location_match = (
                location_match
                or bool(
                    route.get(
                        "location_match",
                        False,
                    )
                )
            )

            analyzed += cls._int(
                route.get(
                    "routes_analyzed",
                    0,
                )
            )

            disrupted += cls._int(
                route.get(
                    "disrupted_routes",
                    0,
                )
            )

            normal = max(
                normal,
                cls._number(
                    route.get(
                        "normal_transit_days",
                        0,
                    )
                ),
            )

            additional = max(
                additional,
                cls._number(
                    route.get(
                        "additional_disruption_delay_days",
                        route.get(
                            "route_delay_days",
                            0,
                        ),
                    )
                ),
            )

            effective_value = cls._number(
                route.get(
                    "effective_route_time_days",
                    0,
                )
            )

            if effective_value <= 0:
                effective_value = cls._number(
                    route.get(
                        "effective_delay_days",
                        0,
                    )
                )

            if (
                effective_value <= 0
                and normal > 0
            ):
                effective_value = (
                    normal
                    + additional
                )

            effective = max(
                effective,
                effective_value,
            )

            route_delay = max(
                route_delay,
                cls._number(
                    route.get(
                        "route_delay_days",
                        additional,
                    )
                ),
            )

            effective_delay = max(
                effective_delay,
                cls._number(
                    route.get(
                        "effective_delay_days",
                        effective_value,
                    )
                ),
            )

        return IntelligenceRouteImpact(
            routes_known=known,
            location_match=location_match,
            routes_analyzed=analyzed,
            disrupted_routes=disrupted,
            normal_transit_days=round(
                normal,
                2,
            ),
            additional_disruption_delay_days=round(
                additional,
                2,
            ),
            effective_route_time_days=round(
                effective,
                2,
            ),
            route_delay_days=round(
                route_delay,
                2,
            ),
            effective_delay_days=round(
                effective_delay,
                2,
            ),
        )

    # ========================================================
    # RESILIENCE
    # ========================================================

    @classmethod
    def _build_resilience(
        cls,
        raw: dict[str, Any],
    ) -> IntelligenceResilience:

        business = cls._dict(
            raw.get(
                "business_supply_chain"
            )
        )

        simulations = cls._get_simulations(
            business
        )

        if not simulations:
            return IntelligenceResilience()

        recovery = 0.0
        unrecovered = 0.0
        gross_lost = 0.0

        alternative_supplier_ids: set[str] = set()

        supplier_id: str | None = None
        supplier_name: str | None = None

        for item in simulations:

            simulation = cls._get_simulation(
                item
            )

            supplier = cls._dict(
                item.get(
                    "supplier"
                )
            )

            if not supplier:
                supplier = cls._dict(
                    simulation.get(
                        "supplier"
                    )
                )

            if supplier:

                supplier_id = (
                    supplier_id
                    or cls._string_or_none(
                        supplier.get(
                            "supplier_id"
                        )
                    )
                )

                supplier_name = (
                    supplier_name
                    or cls._string_or_none(
                        supplier.get(
                            "name"
                        )
                    )
                )

            summary = cls._dict(
                simulation.get(
                    "summary"
                )
            )

            components = simulation.get(
                "components",
                [],
            )

            if not isinstance(
                components,
                list,
            ):
                components = []

            for component in components:

                if not isinstance(
                    component,
                    dict,
                ):
                    continue

                lost = cls._number(
                    component.get(
                        "gross_lost_supply",
                        0,
                    )
                )

                recovered = cls._number(
                    component.get(
                        "alternative_recovery",
                        0,
                    )
                )

                gross_lost += lost
                recovery += recovered

                unrecovered += max(
                    0.0,
                    lost - recovered,
                )

                alternatives = component.get(
                    "alternative_suppliers",
                    [],
                )

                if isinstance(
                    alternatives,
                    list,
                ):

                    for alternative in alternatives:

                        if not isinstance(
                            alternative,
                            dict,
                        ):
                            continue

                        alternative_id = (
                            cls._string_or_none(
                                alternative.get(
                                    "supplier_id"
                                )
                            )
                        )

                        if alternative_id:
                            alternative_supplier_ids.add(
                                alternative_id
                            )

            if not components and summary:

                gross_lost += cls._number(
                    summary.get(
                        "gross_lost_supply",
                        0,
                    )
                )

                recovery += cls._number(
                    summary.get(
                        "alternative_recovery",
                        0,
                    )
                )

                unrecovered += cls._number(
                    summary.get(
                        "gross_shortage",
                        0,
                    )
                )

        if gross_lost <= 0:

            return IntelligenceResilience(
                available=False,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
            )

        percentage = (
            recovery
            / gross_lost
            * 100.0
        )

        score = min(
            100.0,
            percentage,
        )

        level = cls._resilience_level(
            score
        )

        return IntelligenceResilience(
            available=True,
            recovery_units=round(
                recovery,
                2,
            ),
            unrecovered_units=round(
                unrecovered,
                2,
            ),
            recovery_percentage=round(
                percentage,
                2,
            ),
            resilience_score=round(
                score,
                2,
            ),
            resilience_level=level,
            alternative_supplier_count=len(
                alternative_supplier_ids
            ),
            supplier_id=supplier_id,
            supplier_name=supplier_name,
        )

    # ========================================================
    # RISK
    # ========================================================

    @classmethod
    def _build_risk(
        cls,
        raw: dict[str, Any],
    ) -> IntelligenceRisk:
        """
        Build the canonical business risk.

        IMPORTANT:

        Business simulation risk is authoritative for the
        operational/business-impact risk shown by AtmoGraph.

        Prediction models remain separate under `prediction`.

        Priority:

            1. business_supply_chain.summary.max_risk_score
            2. business simulation summary.max_risk_score
            3. business simulation component risk_score
            4. base prediction risk_score
            5. hybrid prediction risk_score
            6. unknown

        Missing information must remain `unknown`.
        """

        business = cls._dict(
            raw.get(
                "business_supply_chain"
            )
        )

        top_summary = cls._dict(
            business.get(
                "summary"
            )
        )

        simulation_container = cls._dict(
            business.get(
                "simulation"
            )
        )

        simulations = cls._get_simulations(
            business
        )

        prediction = cls._dict(
            raw.get(
                "prediction"
            )
        )

        base = cls._dict(
            prediction.get(
                "base_prediction"
            )
        )

        hybrid = cls._dict(
            prediction.get(
                "hybrid_prediction"
            )
        )

        # ----------------------------------------------------
        # BUSINESS RISK
        # ----------------------------------------------------

        business_risk = cls._first_present(
            top_summary.get(
                "max_risk_score"
            ),
            top_summary.get(
                "max_risk"
            ),
            simulation_container.get(
                "max_risk_score"
            ),
            simulation_container.get(
                "max_risk"
            ),
        )

        # ----------------------------------------------------
        # If the top-level business summary is unavailable,
        # inspect every nested simulation summary.
        # ----------------------------------------------------

        if business_risk is None:

            nested_risk_scores: list[float] = []

            for item in simulations:

                simulation = cls._get_simulation(
                    item
                )

                summary = cls._dict(
                    simulation.get(
                        "summary"
                    )
                )

                value = cls._first_present(
                    summary.get(
                        "max_risk_score"
                    ),
                    summary.get(
                        "max_risk"
                    ),
                )

                if value is not None:
                    nested_risk_scores.append(
                        cls._number(
                            value
                        )
                    )

                # Some older simulation structures expose
                # risk_score directly on components.
                components = simulation.get(
                    "components",
                    [],
                )

                if isinstance(
                    components,
                    list,
                ):

                    for component in components:

                        if not isinstance(
                            component,
                            dict,
                        ):
                            continue

                        component_risk = (
                            component.get(
                                "risk_score"
                            )
                        )

                        if component_risk is not None:
                            nested_risk_scores.append(
                                cls._number(
                                    component_risk
                                )
                            )

            if nested_risk_scores:

                business_risk = max(
                    nested_risk_scores
                )

        # ----------------------------------------------------
        # Prediction fallback
        # ----------------------------------------------------

        base_risk = cls._first_present(
            base.get(
                "risk_score"
            ),
            prediction.get(
                "risk_score"
            ),
        )

        hybrid_risk = hybrid.get(
            "risk_score"
        )

        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        if business_risk is not None:

            score = cls._number(
                business_risk
            )

            risk_known = True

        elif base_risk is not None:

            score = cls._number(
                base_risk
            )

            risk_known = True

        elif hybrid_risk is not None:

            score = cls._number(
                hybrid_risk
            )

            risk_known = True

        else:

            score = 0.0
            risk_known = False

        # ----------------------------------------------------
        # LEVEL
        # ----------------------------------------------------

        if risk_known:

            level = cls._risk_level(
                score
            )

        else:

            level = "unknown"

        # ----------------------------------------------------
        # PRODUCTION STOP
        # ----------------------------------------------------

        production_stop_value = cls._first_present(
            top_summary.get(
                "production_stop"
            ),
            simulation_container.get(
                "production_stop"
            ),
        )

        if production_stop_value is None:

            production_stop_value = False

            for item in simulations:

                simulation = cls._get_simulation(
                    item
                )

                summary = cls._dict(
                    simulation.get(
                        "summary"
                    )
                )

                if bool(
                    summary.get(
                        "production_stop",
                        False,
                    )
                ):
                    production_stop_value = True
                    break

        production_stop = bool(
            production_stop_value
        )

        # ----------------------------------------------------
        # EXPLANATION / BASIS
        # ----------------------------------------------------

        basis: list[str] = []

        if not risk_known:

            basis.append(
                "Risk score is unavailable from the current intelligence data."
            )

        else:

            if score >= 70:

                basis.append(
                    "High modeled supply-chain risk."
                )

            elif score >= 40:

                basis.append(
                    "Moderate modeled supply-chain risk."
                )

            else:

                basis.append(
                    "Low modeled supply-chain risk."
                )

        if production_stop:

            basis.append(
                "Production-stop condition detected."
            )

        route = cls._build_route_impact(
            raw
        )

        if (
            route.additional_disruption_delay_days
            > 0
        ):

            basis.append(
                "Disruption introduces additional route delay."
            )

        if route.routes_known:

            basis.append(
                "Explicit supply-chain route data is available."
            )

        return IntelligenceRisk(
            score=round(
                score,
                2,
            ),
            level=level,
            production_stop=production_stop,
            confidence=None,
            basis=basis,
        )

    # ========================================================
    # PREDICTION
    # ========================================================

    @classmethod
    def _build_prediction(
        cls,
        raw: dict[str, Any],
    ) -> IntelligencePrediction:

        prediction = cls._dict(
            raw.get(
                "prediction"
            )
        )

        hybrid = cls._dict(
            prediction.get(
                "hybrid_prediction"
            )
        )

        base = cls._dict(
            prediction.get(
                "base_prediction"
            )
        )

        gnn = cls._dict(
            prediction.get(
                "gnn_prediction"
            )
        )

        available = bool(
            prediction
        )

        score = cls._number(
            cls._first_present(
                hybrid.get(
                    "risk_score"
                ),
                base.get(
                    "risk_score"
                ),
                prediction.get(
                    "risk_score"
                ),
                0,
            )
        )

        level = str(
            cls._first_present(
                hybrid.get(
                    "risk_level"
                ),
                base.get(
                    "risk_level"
                ),
                "unknown",
            )
            or "unknown"
        )

        delay = cls._number(
            cls._first_present(
                base.get(
                    "estimated_delay_days"
                ),
                prediction.get(
                    "estimated_delay_days"
                ),
                0,
            )
        )

        return IntelligencePrediction(
            available=available,
            risk_score=round(
                score,
                2,
            ),
            risk_level=level,
            estimated_delay_days=round(
                delay,
                2,
            ),
            model=cls._string_or_none(
                gnn.get(
                    "model"
                )
            ),
            model_loaded=(
                bool(
                    gnn.get(
                        "model_loaded"
                    )
                )
                if "model_loaded" in gnn
                else None
            ),
        )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    @classmethod
    def _build_recommendations(
        cls,
        raw: dict[str, Any],
    ) -> list[str]:

        business = cls._build_business_impact(
            raw
        )

        route = cls._build_route_impact(
            raw
        )

        resilience = cls._build_resilience(
            raw
        )

        recommendations: list[str] = []

        if business.production_stop:

            recommendations.append(
                "Prioritize immediate production-continuity actions."
            )

        if business.net_shortage > 0:

            recommendations.append(
                "Activate alternate supply or procurement recovery for the remaining shortage."
            )

        elif (
            business.gross_shortage > 0
            and business.net_shortage <= 0
        ):

            recommendations.append(
                "Inventory currently buffers the modeled shortage; monitor inventory burn-down."
            )

        if (
            route.additional_disruption_delay_days
            > 0
        ):

            recommendations.append(
                "Review affected logistics routes and consider alternate transportation paths."
            )

        if (
            resilience.available
            and resilience.recovery_percentage
            < 50
        ):

            recommendations.append(
                "Increase alternate-supplier capacity because recovery coverage is below 50%."
            )

        if not recommendations:

            recommendations.append(
                "Continue monitoring the affected supply-chain dependencies."
            )

        return recommendations

    # ========================================================
    # SIMULATION HELPERS
    # ========================================================

    @classmethod
    def _get_simulations(
        cls,
        business: dict[str, Any],
    ) -> list[dict[str, Any]]:

        simulation_container = business.get(
            "simulation",
            business.get(
                "simulations",
                [],
            ),
        )

        if isinstance(
            simulation_container,
            dict,
        ):

            simulations = simulation_container.get(
                "simulations",
                [],
            )

        else:

            simulations = simulation_container

        if not isinstance(
            simulations,
            list,
        ):
            return []

        return [
            item
            for item in simulations
            if isinstance(
                item,
                dict,
            )
        ]

    @classmethod
    def _get_simulation(
        cls,
        item: dict[str, Any],
    ) -> dict[str, Any]:

        simulation = item.get(
            "simulation"
        )

        if isinstance(
            simulation,
            dict,
        ):
            return simulation

        return item

    @classmethod
    def _aggregate_simulations(
        cls,
        simulations: list[dict[str, Any]],
    ) -> dict[str, Any]:

        result = {
            "affected_components": 0,
            "affected_products": 0,
            "affected_plants": 0,
            "gross_lost_supply": 0.0,
            "alternative_recovery": 0.0,
            "gross_shortage": 0.0,
            "net_shortage": 0.0,
            "products_buffered": 0,
            "products_route_delayed": 0,
            "products_with_shortage": 0,
            "production_stop": False,
            "max_delay_days": 0.0,
            "max_route_disruption_delay_days": 0.0,
            "max_risk_score": 0.0,
        }

        for item in simulations:

            simulation = cls._get_simulation(
                item
            )

            summary = cls._dict(
                simulation.get(
                    "summary"
                )
            )

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

            if isinstance(
                components,
                list,
            ):

                result[
                    "affected_components"
                ] += len(
                    components
                )

            if isinstance(
                products,
                list,
            ):

                result[
                    "affected_products"
                ] += len(
                    products
                )

            if isinstance(
                plants,
                list,
            ):

                result[
                    "affected_plants"
                ] += len(
                    plants
                )

            for key in (
                "gross_lost_supply",
                "alternative_recovery",
                "gross_shortage",
                "net_shortage",
            ):

                result[key] += cls._number(
                    summary.get(
                        key,
                        0,
                    )
                )

            result[
                "products_buffered"
            ] += cls._int(
                summary.get(
                    "products_buffered",
                    0,
                )
            )

            result[
                "products_route_delayed"
            ] += cls._int(
                summary.get(
                    "products_route_delayed",
                    0,
                )
            )

            result[
                "products_with_shortage"
            ] += cls._int(
                summary.get(
                    "products_with_shortage",
                    0,
                )
            )

            result[
                "production_stop"
            ] = (
                result[
                    "production_stop"
                ]
                or bool(
                    summary.get(
                        "production_stop",
                        False,
                    )
                )
            )

            result[
                "max_delay_days"
            ] = max(
                result[
                    "max_delay_days"
                ],
                cls._number(
                    summary.get(
                        "max_delay_days",
                        0,
                    )
                ),
            )

            result[
                "max_route_disruption_delay_days"
            ] = max(
                result[
                    "max_route_disruption_delay_days"
                ],
                cls._number(
                    summary.get(
                        "max_route_disruption_delay_days",
                        0,
                    )
                ),
            )

            result[
                "max_risk_score"
            ] = max(
                result[
                    "max_risk_score"
                ],
                cls._number(
                    summary.get(
                        "max_risk_score",
                        summary.get(
                            "max_risk",
                            0,
                        ),
                    )
                ),
            )

        return result

    # ========================================================
    # GENERAL HELPERS
    # ========================================================

    @staticmethod
    def _dict(
        value: Any,
    ) -> dict[str, Any]:

        return (
            value
            if isinstance(
                value,
                dict,
            )
            else {}
        )

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:

            return max(
                0.0,
                float(
                    value or 0
                ),
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

            return max(
                0,
                int(
                    float(
                        value or 0
                    )
                ),
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0

    @staticmethod
    def _int_or_none(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        try:

            return int(
                float(value)
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _first_number_or_none(
        *values: Any,
    ) -> float | None:

        for value in values:

            if value is None:
                continue

            try:

                return float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

        return None

    @staticmethod
    def _first_present(
        *values: Any,
    ) -> Any:

        for value in values:

            if value is not None:
                return value

        return None

    @staticmethod
    def _string_or_none(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        text = str(
            value
        ).strip()

        return text or None

    @staticmethod
    def _dedupe_entities(
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        result: list[dict[str, Any]] = []
        seen: set[str] = set()

        for entity in entities:

            key = str(
                entity.get(
                    "supplier_id",
                    entity.get(
                        "id",
                        entity.get(
                            "name",
                            "",
                        ),
                    ),
                )
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(
                entity
            )

        return result

    @staticmethod
    def _risk_level(
        score: float,
    ) -> str:

        if score >= 80:
            return "critical"

        if score >= 60:
            return "high"

        if score >= 40:
            return "medium"

        return "low"

    @staticmethod
    def _resilience_level(
        score: float,
    ) -> str:

        if score >= 70:
            return "resilient"

        if score >= 45:
            return "moderate"

        if score >= 20:
            return "high_risk"

        return "critical_risk"


__all__ = [
    "UnifiedIntelligenceService",
]