from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.business_supply_chain import (
    BusinessSupplier,
    Plant,
    Route,
)


class RouteImpactService:
    """
    Event-aware route intelligence.

    Responsibilities:
    - Find explicit routes belonging to a supplier.
    - Determine whether an event affects those routes.
    - Separate normal transit time from disruption-added delay.
    - Never invent a route.
    - Never treat normal transit time as disruption delay.

    Route timing semantics:

        normal_transit_days
            = normal route transit time from the dataset.

        additional_disruption_delay_days
            = extra delay caused by the disruption event.

        effective_route_time_days
            = normal_transit_days + additional_disruption_delay_days.

    Backward-compatible fields:

        route_delay_days
            = additional disruption delay.

        effective_delay_days
            = total effective route time.

    Example:

        Normal transit = 14 days
        Event delay    = 10 days

        route_delay_days          = 10
        effective_route_time_days = 24
    """

    SEVERITY_DELAY = {
        "critical": 14.0,
        "high": 10.0,
        "medium": 7.0,
        "low": 3.0,
    }

    DISRUPTED_ROUTE_STATUSES = {
        "disrupted",
        "blocked",
        "closed",
        "cancelled",
        "canceled",
        "suspended",
        "delayed",
        "congested",
    }

    def __init__(self, db: Session, user_id: int | None = None) -> None:
        self.db = db
        self.user_id = user_id

    def _query(self, model):
        query = self.db.query(model)
        if self.user_id is not None:
            query = query.filter(model.user_id == self.user_id)
        return query

    # =========================================================
    # PUBLIC
    # =========================================================

    def analyze_supplier_routes(
        self,
        supplier_id: str,
        disruption_location: str | None = None,
        severity: str | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze all explicitly known routes associated with a supplier.

        Important:
        - No route is fabricated.
        - Normal transit and disruption delay remain separate.
        """

        supplier = (
            self._query(BusinessSupplier)
            .filter(
                BusinessSupplier.supplier_id == supplier_id
            )
            .first()
        )

        if supplier is None:
            return {
                "success": False,
                "supplier_id": supplier_id,
                "routes_known": False,
                "routes_analyzed": 0,
                "disrupted_routes": 0,
                "location_match": False,

                # Backward-compatible fields.
                "route_delay_days": 0.0,
                "effective_delay_days": 0.0,

                # New explicit semantics.
                "normal_transit_days": 0.0,
                "additional_disruption_delay_days": 0.0,
                "effective_route_time_days": 0.0,

                "routes": [],
                "message": "Supplier not found.",
            }

        # -----------------------------------------------------
        # Outbound routes:
        # supplier -> destination
        # -----------------------------------------------------

        outbound_routes = (
            self._query(Route)
            .filter(
                Route.source_type.ilike("supplier"),
                Route.source_id == supplier_id,
            )
            .all()
        )

        # -----------------------------------------------------
        # Inbound routes:
        # destination -> supplier
        # -----------------------------------------------------

        inbound_routes = (
            self._query(Route)
            .filter(
                Route.destination_type.ilike("supplier"),
                Route.destination_id == supplier_id,
            )
            .all()
        )

        # -----------------------------------------------------
        # Merge without duplicates.
        # -----------------------------------------------------

        existing_route_ids = {
            route.route_id
            for route in outbound_routes
        }

        all_routes = list(outbound_routes)

        for route in inbound_routes:
            if route.route_id not in existing_route_ids:
                all_routes.append(route)

        # -----------------------------------------------------
        # No explicit route.
        # -----------------------------------------------------

        if not all_routes:
            return {
                "success": True,
                "supplier_id": supplier_id,
                "routes_known": False,
                "routes_analyzed": 0,
                "disrupted_routes": 0,
                "location_match": False,

                # No route means no route timing can be claimed.
                "normal_transit_days": 0.0,
                "additional_disruption_delay_days": 0.0,
                "effective_route_time_days": 0.0,

                # Backward compatibility.
                "route_delay_days": 0.0,
                "effective_delay_days": 0.0,

                "routes": [],
                "message": (
                    "No explicit route is available for this supplier."
                ),
            }

        # -----------------------------------------------------
        # Event context.
        # -----------------------------------------------------

        location = self._normalize(
            disruption_location
        )

        event_severity = (
            str(severity or "medium")
            .strip()
            .lower()
        )

        base_event_delay = self.SEVERITY_DELAY.get(
            event_severity,
            7.0,
        )

        event_kind = self._normalize(
            event_type
        )

        analyzed_routes: list[dict[str, Any]] = []

        # IMPORTANT:
        # These are intentionally different metrics.
        #
        # max_normal_transit:
        #     normal route time.
        #
        # max_disruption_delay:
        #     ONLY additional event-caused delay.
        #
        # max_effective_route_time:
        #     normal transit + additional disruption delay.
        #
        max_normal_transit = 0.0
        max_disruption_delay = 0.0
        max_effective_route_time = 0.0

        location_match = False

        for route in all_routes:

            destination = self._resolve_destination(
                route
            )

            # -------------------------------------------------
            # Does event location match a known endpoint?
            # -------------------------------------------------

            route_location_match = (
                self._route_matches_location(
                    route=route,
                    supplier=supplier,
                    disruption_location=location,
                )
            )

            # -------------------------------------------------
            # Is route already explicitly marked disrupted?
            # -------------------------------------------------

            explicit_disruption = (
                self._is_disrupted_status(
                    route.route_status
                )
            )

            # -------------------------------------------------
            # Event category.
            # -------------------------------------------------

            port_event = (
                "port" in event_kind
                or "harbor" in event_kind
                or "shipping" in event_kind
                or "logistics" in event_kind
                or "congestion" in event_kind
            )

            # -------------------------------------------------
            # A route is disrupted when:
            #
            # 1. Event location matches a known endpoint, OR
            # 2. Dataset explicitly marks route as disrupted.
            #
            # We do NOT infer a route merely because the event
            # happens somewhere in the same country/region.
            # -------------------------------------------------

            disrupted = (
                route_location_match
                or explicit_disruption
            )

            if route_location_match:
                location_match = True

            # -------------------------------------------------
            # Normal transit time.
            # -------------------------------------------------

            transit_days = self._number(
                route.transit_days
            )

            # -------------------------------------------------
            # Additional disruption delay.
            #
            # This is the ONLY value that represents the event's
            # added delay.
            # -------------------------------------------------

            disruption_delay = 0.0

            if route_location_match:
                disruption_delay = base_event_delay

            elif explicit_disruption:
                # Existing route status indicates disruption,
                # but without a direct event-location match we
                # use a conservative half-severity delay.
                disruption_delay = (
                    base_event_delay * 0.5
                )

            # -------------------------------------------------
            # Effective route time.
            #
            # Example:
            # transit = 14
            # disruption = 10
            # effective = 24
            #
            # If the route is not disrupted, we DO NOT expose
            # 14 as an "effective delay".
            # -------------------------------------------------

            effective_route_time = (
                transit_days + disruption_delay
                if disrupted
                else transit_days
            )

            # -------------------------------------------------
            # Aggregate metrics.
            #
            # VERY IMPORTANT:
            # max_disruption_delay receives ONLY
            # disruption_delay, NOT effective_route_time.
            # -------------------------------------------------

            max_normal_transit = max(
                max_normal_transit,
                transit_days,
            )

            max_disruption_delay = max(
                max_disruption_delay,
                disruption_delay,
            )

# -------------------------------------------------
# Aggregate effective route time.
#
# effective_route_time_days always represents the
# actual route travel time:
#
# normal route:
#     14 + 0 = 14
#
# disrupted route:
#     14 + 10 = 24
#
# It must NOT become zero merely because the
# current event does not disrupt the route.
# -------------------------------------------------

            max_effective_route_time = max(
                max_effective_route_time,
                effective_route_time,
            )

            # -------------------------------------------------
            # Route result.
            # -------------------------------------------------

            analyzed_routes.append(
                {
                    "route_id": route.route_id,
                    "source_type": route.source_type,
                    "source_id": route.source_id,

                    "destination_type": (
                        route.destination_type
                    ),
                    "destination_id": (
                        route.destination_id
                    ),
                    "destination_name": destination,

                    # -----------------------------------------
                    # Timing — explicit new semantics.
                    # -----------------------------------------

                    "normal_transit_days": round(
                        transit_days,
                        2,
                    ),

                    "additional_disruption_delay_days": round(
                        disruption_delay,
                        2,
                    ),

                    "effective_route_time_days": round(
                        effective_route_time,
                        2,
                    ),

                    # -----------------------------------------
                    # Existing field retained for compatibility.
                    #
                    # IMPORTANT:
                    # route_delay_days = EXTRA delay only.
                    # It must NOT be 24 when transit is 14
                    # and disruption is 10.
                    # -----------------------------------------

                    "transit_days": round(
                        transit_days,
                        2,
                    ),

                    "route_delay_days": round(
                        disruption_delay,
                        2,
                    ),

                    "route_disruption_delay_days": round(
                        disruption_delay,
                        2,
                    ),

                    "effective_delay_days": round(
                        effective_route_time,
                        2,
                    ),

                    # -----------------------------------------
                    # Route state.
                    # -----------------------------------------

                    "route_status": (
                        route.route_status
                    ),

                    "location_match": (
                        route_location_match
                    ),

                    "explicitly_disrupted": (
                        explicit_disruption
                    ),

                    "disrupted": disrupted,

                    "event_type": event_type,

                    "port_or_logistics_event": (
                        port_event
                    ),

                    "event_delay_days": round(
                        disruption_delay,
                        2,
                    ),
                }
            )

        # =====================================================
        # FINAL RESULT
        # =====================================================

        return {
            "success": True,
            "supplier_id": supplier_id,

            "routes_known": True,

            "location_match": location_match,

            "routes_analyzed": len(
                analyzed_routes
            ),

            "disrupted_routes": sum(
                1
                for route in analyzed_routes
                if route["disrupted"]
            ),

            # =================================================
            # Correct top-level timing semantics.
            # =================================================

            "normal_transit_days": round(
                max_normal_transit,
                2,
            ),

            "additional_disruption_delay_days": round(
                max_disruption_delay,
                2,
            ),

            "effective_route_time_days": round(
                max_effective_route_time,
                2,
            ),

            # =================================================
            # Backward-compatible fields.
            #
            # route_delay_days MUST mean additional delay.
            # effective_delay_days means total effective time.
            # =================================================

            "route_delay_days": round(
                max_disruption_delay,
                2,
            ),

            "effective_delay_days": round(
                max_effective_route_time,
                2,
            ),

            "routes": analyzed_routes,
        }

    # =========================================================
    # LOCATION MATCHING
    # =========================================================

    def _route_matches_location(
        self,
        route: Route,
        supplier: BusinessSupplier,
        disruption_location: str,
    ) -> bool:
        """
        Match disruption location against known route endpoints.

        We only use locations actually present in the dataset.

        Known locations:
        - supplier city
        - supplier country
        - destination city
        - destination country

        No route or location is fabricated.
        """

        if not disruption_location:
            return False

        candidates = [
            supplier.city,
            supplier.country,
        ]

        destination = self._resolve_destination_object(
            route
        )

        if destination is not None:
            candidates.extend(
                [
                    getattr(
                        destination,
                        "city",
                        None,
                    ),
                    getattr(
                        destination,
                        "country",
                        None,
                    ),
                ]
            )

        normalized_candidates = {
            self._normalize(value)
            for value in candidates
            if value
        }

        normalized_candidates.discard("")

        if not normalized_candidates:
            return False

        # Exact match.
        if disruption_location in normalized_candidates:
            return True

        # Word-boundary match.
        for candidate in normalized_candidates:

            if re.search(
                rf"\b{re.escape(candidate)}\b",
                disruption_location,
            ):
                return True

            if re.search(
                rf"\b{re.escape(disruption_location)}\b",
                candidate,
            ):
                return True

        return False

    # =========================================================
    # ROUTE DESTINATION
    # =========================================================

    def _resolve_destination(
        self,
        route: Route,
    ) -> str | None:
        """
        Resolve destination display name.
        """

        obj = self._resolve_destination_object(
            route
        )

        if obj is None:
            return None

        return (
            getattr(
                obj,
                "plant_name",
                None,
            )
            or getattr(
                obj,
                "warehouse_name",
                None,
            )
            or getattr(
                obj,
                "supplier_name",
                None,
            )
            or getattr(
                obj,
                "company_name",
                None,
            )
        )

    def _resolve_destination_object(
        self,
        route: Route,
    ) -> Any | None:
        """
        Resolve known destination entity.

        Currently supports:
        - plant
        - supplier

        Other entity types intentionally return None rather
        than fabricating information.
        """

        destination_type = (
            str(
                route.destination_type or ""
            )
            .strip()
            .lower()
        )

        destination_id = str(
            route.destination_id
        )

        if destination_type == "plant":
            return (
                self._query(Plant)
                .filter(
                    Plant.plant_id
                    == destination_id
                )
                .first()
            )

        if destination_type == "supplier":
            return (
                self._query(BusinessSupplier)
                .filter(
                    BusinessSupplier.supplier_id
                    == destination_id
                )
                .first()
            )

        return None

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:
        """
        Normalize text for safe location comparison.
        """

        if not value:
            return ""

        value = str(
            value
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        """
        Safely convert numeric values to non-negative float.
        """

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

    @classmethod
    def _is_disrupted_status(
        cls,
        status: str | None,
    ) -> bool:
        """
        Check whether a route is explicitly marked as disrupted.
        """

        if not status:
            return False

        normalized = (
            str(status)
            .strip()
            .lower()
        )

        return normalized in (
            cls.DISRUPTED_ROUTE_STATUSES
        )


__all__ = [
    "RouteImpactService",
]