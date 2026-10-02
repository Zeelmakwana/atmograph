from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.supply_chain import Supplier, Product
from app.models.supply_chain_link import SupplyChainLink
from app.models.business_supply_chain import BusinessSupplier

from app.services.nlp_engine import nlp_engine
from app.services.neo4j_service import Neo4jService
from app.services.prediction_engine import predict_event_impact
from app.services.location_resolution_service import (
    LocationResolutionService,
)
from app.services.hybrid_prediction_service import HybridPredictionService
from app.services.supply_chain.disruption_simulator import (
    DisruptionSimulator,
)


class IntelligencePipeline:
    """
    Complete AtmoGraph intelligence pipeline.

    NEWS
        ↓
    NLP
        ↓
    SQL EVENT
        ↓
    CANONICAL ENTITY MATCHING
        ↓
    BUSINESS SUPPLIER MATCHING
        ↓
    EVENT CONTEXT
        ↓
    ROUTE-AWARE DISRUPTION SIMULATION
        ↓
    INVENTORY / ALTERNATIVE SUPPLY
        ↓
    PLANT / PRODUCT IMPACT
        ↓
    NEO4J
        ↓
    PREDICTION

    Important matching rule:

    Exact supplier identity has priority.

    Generic words such as:
        components
        systems
        company
        global
        backup
        india

    must never independently identify a supplier.

    Important intelligence rule:

    Unknown route / dependency information remains UNKNOWN.
    The pipeline must not invent a route just because a
    disruption location appears in the news.
    """

    def __init__(self, db: Session, user_id: int | None = None) -> None:
        self.db = db
        self.user_id = user_id
        self.neo4j = Neo4jService()

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:

        if not value:
            return ""

        value = str(value).lower().strip()

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

    # =========================================================
    # MEANINGFUL TOKENS
    # =========================================================

    @staticmethod
    def _meaningful_tokens(
        value: str | None,
    ) -> set[str]:

        if not value:
            return set()

        stop_words = {
            "the",
            "and",
            "for",
            "from",
            "with",
            "that",
            "this",
            "into",
            "during",
            "after",
            "before",

            # Corporate suffixes.
            "ltd",
            "limited",
            "inc",
            "incorporated",
            "co",
            "company",
            "corp",
            "corporation",

            # Generic business words.
            "group",
            "global",
            "backup",
            "systems",
            "india",
            "international",
            "industries",
            "industrial",
            "holdings",
        }

        tokens = set(
            str(value).split()
        )

        return {
            token
            for token in tokens
            if len(token) >= 4
            and token not in stop_words
        }

    # =========================================================
    # ENTITY SIMILARITY
    # =========================================================

    @classmethod
    def _entity_similarity(
        cls,
        entity: str,
        supplier_name: str,
    ) -> float:
        """
        Calculate conservative normalized similarity between
        an extracted organization and a canonical supplier name.

        Corporate suffix differences such as:

            Ltd
            Limited
            Inc
            Incorporated
            Company

        are ignored through meaningful-token comparison.

        The raw normalized text similarity is also considered,
        but similarity alone is NEVER sufficient for matching.
        A meaningful shared token is required.
        """

        normalized_entity = cls._normalize(
            entity
        )

        normalized_supplier = cls._normalize(
            supplier_name
        )

        if not normalized_entity:
            return 0.0

        if not normalized_supplier:
            return 0.0

        if normalized_entity == normalized_supplier:
            return 1.0

        entity_tokens = cls._meaningful_tokens(
            normalized_entity
        )

        supplier_tokens = cls._meaningful_tokens(
            normalized_supplier
        )

        if not entity_tokens:
            return 0.0

        if not supplier_tokens:
            return 0.0

        token_overlap = (
            len(
                entity_tokens
                & supplier_tokens
            )
            / max(
                len(entity_tokens),
                len(supplier_tokens),
            )
        )

        raw_similarity = SequenceMatcher(
            None,
            normalized_entity,
            normalized_supplier,
        ).ratio()

        token_text_entity = " ".join(
            sorted(entity_tokens)
        )

        token_text_supplier = " ".join(
            sorted(supplier_tokens)
        )

        token_similarity = SequenceMatcher(
            None,
            token_text_entity,
            token_text_supplier,
        ).ratio()

        return max(
            raw_similarity,
            token_similarity * 0.95,
            token_overlap * 0.90,
        )

    # =========================================================
    # ENTITY TOKEN VALIDATION
    # =========================================================

    @classmethod
    def _strong_entity_match(cls, entity: str, supplier_name: str) -> bool:
        normalized_entity = cls._normalize(entity)
        normalized_supplier = cls._normalize(supplier_name)

        if not normalized_entity or not normalized_supplier:
            return False

        # Exact normalized match.
        if normalized_entity == normalized_supplier:
            return True

        # Company suffix normalization:
        # "Limited" == "Ltd", "Company" == "Co", etc.
        def company_core(value: str) -> str:
            suffix_pattern = (
                r"\b(limited|ltd|incorporated|inc|company|co|"
                r"corporation|corp|llc|plc)\b"
            )
            return re.sub(r"\s+", " ", re.sub(suffix_pattern, "", value)).strip()

        entity_core = company_core(normalized_entity)
        supplier_core = company_core(normalized_supplier)

        # Example:
        # Global Components Limited -> global components
        # Global Components Ltd     -> global components
        if entity_core and supplier_core and entity_core == supplier_core:
            return True

        entity_tokens = cls._meaningful_tokens(normalized_entity)
        supplier_tokens = cls._meaningful_tokens(normalized_supplier)

        if not entity_tokens or not supplier_tokens:
            return False

        shared_tokens = entity_tokens & supplier_tokens

        # A single generic token must never identify a supplier.
        if len(shared_tokens) < 2:
            return False

        # Multi-token entity contained inside supplier name.
        # Example:
        # "Backup Components" -> "Backup Components India"
        if (
            len(entity_tokens) >= 2
            and shared_tokens == entity_tokens
        ):
            return True

        # Supplier's meaningful name contained inside extracted entity.
        if (
            len(supplier_tokens) >= 2
            and shared_tokens == supplier_tokens
        ):
            return True

        similarity = cls._entity_similarity(
            normalized_entity,
            normalized_supplier,
        )

        return similarity >= 0.88 and len(shared_tokens) >= 2

    # =========================================================
    # BUSINESS SUPPLIER MATCHING
    # =========================================================

    # =========================================================
    # STRICT SUPPLIER MATCH SCORE
    # =========================================================

    @classmethod
    def _supplier_match_score(
        cls,
        text: str,
        supplier_name: str,
        supplier_city: str | None,
        supplier_country: str | None,
        nlp_entities: list[str],
        nlp_locations: list[str],
    ) -> tuple[int, list[str]]:

        normalized_text = cls._normalize(text)
        normalized_name = cls._normalize(supplier_name)
        normalized_city = cls._normalize(supplier_city)
        normalized_country = cls._normalize(supplier_country)

        normalized_entities = {
            cls._normalize(entity)
            for entity in nlp_entities
            if entity
        }

        normalized_locations = {
            cls._normalize(location)
            for location in nlp_locations
            if location
        }

        # 1. Exact supplier name.
        if (
            normalized_name
            and normalized_name in normalized_text
        ):
            return (
                100,
                ["supplier_name_exact"],
            )

        # 2. Strong NLP entity.
        for entity in normalized_entities:

            if not entity:
                continue

            if cls._strong_entity_match(
                entity=entity,
                supplier_name=normalized_name,
            ):
                return (
                    95,
                    ["nlp_supplier_entity"],
                )

        # 3. Supporting location evidence.
        city_match = False
        if normalized_city:
            city_tokens = [
                c.strip()
                for c in normalized_city.split()
                if len(c.strip()) >= 3
                and c.strip() not in {
                    "uttar",
                    "pradesh",
                    "gujarat",
                    "maharashtra",
                    "karnataka",
                    "india",
                }
            ]
            if (
                normalized_city in normalized_text
                or normalized_city in normalized_locations
            ):
                city_match = True
            elif any(
                ct in normalized_text
                or ct in normalized_locations
                for ct in city_tokens
            ):
                city_match = True

        country_match = False
        if (
            normalized_country
            and (
                normalized_country in normalized_text
                or normalized_country in normalized_locations
            )
        ):
            country_match = True

        # 4. Token overlap & Disruption keywords
        supplier_tokens = cls._meaningful_tokens(
            normalized_name
        )

        text_tokens = set(
            normalized_text.split()
        )

        overlap = supplier_tokens & text_tokens

        disruption_terms = {
            "flood",
            "flooding",
            "rain",
            "monsoon",
            "downpour",
            "strike",
            "halt",
            "halted",
            "shutdown",
            "closed",
            "delay",
            "delayed",
            "bottleneck",
            "accident",
            "fire",
            "explosion",
            "storm",
            "cyclone",
            "traffic",
            "stoppage",
            "blocked",
            "congestion",
            "disruption",
            "waterlogging",
            "blast",
            "power",
            "grid",
            "outage",
            "failure",
            "damage",
            "curfew",
        }
        has_disruption = bool(
            disruption_terms & text_tokens
        )

        # Match Tier A: 2 or more distinct supplier tokens match
        if len(overlap) >= 2:
            score = 80 + min(len(overlap) * 5, 15)
            reasons = ["supplier_name_tokens"]
            if city_match:
                score = min(score + 5, 95)
                reasons.append("supplier_city")
            return (score, reasons)

        # Match Tier B: At least 1 supplier token + City match
        if len(overlap) >= 1 and city_match:
            return (
                85,
                ["supplier_token_and_city"],
            )

        # Match Tier C: Direct City match during a reported disruption
        if city_match and has_disruption:
            return (
                80,
                ["supplier_city_disrupted"],
            )

        # Match Tier D: Distinctive keyword match (e.g. unique word of length >= 5)
        distinctive_overlap = [
            t for t in overlap if len(t) >= 5
        ]
        if distinctive_overlap:
            return (
                75,
                ["distinctive_keyword_match"],
            )

        return (
            0,
            [],
        )


    def _match_business_suppliers(
        self,
        title: str,
        description: str,
        nlp_result: dict[str, Any],
    ) -> list[dict[str, Any]]:

        full_text = (
            f"{title} {description}"
        )

        bs_query = self.db.query(BusinessSupplier)
        if self.user_id is not None:
            bs_query = bs_query.filter(BusinessSupplier.user_id == self.user_id)
        business_suppliers = (
            bs_query
            .order_by(
                BusinessSupplier.supplier_name.asc()
            )
            .all()
        )

        if not business_suppliers:
            return []

        nlp_entities = [
            str(
                entity.get(
                    "text",
                    "",
                )
            )
            for entity in nlp_result.get(
                "entities",
                [],
            )
            if entity.get("text")
        ]

        nlp_locations = [
            str(location)
            for location in nlp_result.get(
                "locations",
                [],
            )
            if location
        ]

        matches: list[
            dict[str, Any]
        ] = []

        for supplier in business_suppliers:

            score, reasons = (
                self._supplier_match_score(
                    text=full_text,
                    supplier_name=(
                        supplier.supplier_name
                        or ""
                    ),
                    supplier_city=(
                        supplier.city
                    ),
                    supplier_country=(
                        supplier.country
                    ),
                    nlp_entities=nlp_entities,
                    nlp_locations=nlp_locations,
                )
            )

            if score <= 0:
                continue

            location_match = (
                LocationResolutionService
                .resolve_against_entity(
                    raw_location=(
                        next(
                            iter(nlp_locations),
                            None,
                        )
                        if nlp_locations
                        else None
                    ),
                    entity_city=supplier.city,
                    entity_country=supplier.country,
                )
            )

            matches.append(
                {
                    "supplier_id": (
                        supplier.supplier_id
                    ),
                    "name": (
                        supplier.supplier_name
                    ),
                    "country": (
                        supplier.country
                    ),
                    "city": (
                        supplier.city
                    ),
                    "location_known": (
                        supplier.location_known
                    ),

                    "match_score": score,

                    "match_reasons": reasons,

                    "location_match": {
                        "city_match": (
                            location_match.get(
                                "city_match",
                                False,
                            )
                        ),
                        "country_match": (
                            location_match.get(
                                "country_match",
                                False,
                            )
                        ),
                        "match_score": (
                            location_match.get(
                                "match_score",
                                0,
                            )
                        ),
                        "confidence": (
                            location_match.get(
                                "confidence",
                                0.0,
                            )
                        ),
                        "match_level": (
                            location_match.get(
                                "match_level",
                                "no_match",
                            )
                        ),
                        "match_reasons": (
                            location_match.get(
                                "match_reasons",
                                [],
                            )
                        ),
                    },
                }
            )

        matches.sort(
            key=lambda item: (
                -item["match_score"],
                item["name"],
            )
        )

        # High-confidence identity is exclusive.
        exact_matches = [
            item
            for item in matches
            if item["match_score"] >= 90
        ]

        target_list = exact_matches if exact_matches else [
            item
            for item in matches
            if item["match_score"] >= 75
        ]

        seen_ids = set()
        deduped = []
        for item in target_list:
            sid = item.get("supplier_id")
            if sid and sid in seen_ids:
                continue
            if sid:
                seen_ids.add(sid)
            deduped.append(item)

        return deduped

    # =========================================================
    # OLD CANONICAL ENTITY MATCHING
    # =========================================================

    def _match_legacy_entities(
        self,
        title: str,
        description: str,
        nlp_result: dict[str, Any],
    ) -> tuple[
        list[Supplier],
        list[Product],
    ]:

        full_text = (
            f"{title} {description}"
        ).lower()

        suppliers = (
            self.db.query(
                Supplier
            )
            .all()
        )

        products = (
            self.db.query(
                Product
            )
            .all()
        )

        matched_suppliers: list[
            Supplier
        ] = []

        matched_products: list[
            Product
        ] = []

        # =====================================================
        # DIRECT SUPPLIER MATCH
        # =====================================================

        for supplier in suppliers:

            supplier_name = str(
                supplier.name
            ).strip().lower()

            if (
                supplier_name
                and supplier_name
                in full_text
            ):
                matched_suppliers.append(
                    supplier
                )

        # =====================================================
        # DIRECT PRODUCT MATCH
        # =====================================================

        for product in products:

            product_name = str(
                product.name
            ).strip().lower()

            if (
                product_name
                and product_name
                in full_text
            ):
                matched_products.append(
                    product
                )

        # =====================================================
        # NLP ENTITY FALLBACK
        # =====================================================

        entities = nlp_result.get(
            "entities",
            [],
        )

        for entity in entities:

            entity_text = str(
                entity.get(
                    "text",
                    "",
                )
            ).strip().lower()

            if not entity_text:
                continue

            if len(
                self._meaningful_tokens(
                    entity_text
                )
            ) < 2:
                continue

            for supplier in suppliers:

                supplier_name = str(
                    supplier.name
                ).strip().lower()

                if self._strong_entity_match(
                    entity=entity_text,
                    supplier_name=supplier_name,
                ):

                    if (
                        supplier
                        not in matched_suppliers
                    ):
                        matched_suppliers.append(
                            supplier
                        )

            for product in products:

                product_name = str(
                    product.name
                ).strip().lower()

                if (
                    entity_text
                    == product_name
                    or (
                        len(entity_text) >= 8
                        and (
                            entity_text
                            in product_name
                            or product_name
                            in entity_text
                        )
                    )
                ):

                    if (
                        product
                        not in matched_products
                    ):
                        matched_products.append(
                            product
                        )

        # =====================================================
        # INFER SUPPLIER FROM PRODUCT
        # =====================================================

        for product in matched_products:

            if product.supplier_id is None:
                continue

            owner = (
                self.db.query(
                    Supplier
                )
                .filter(
                    Supplier.id
                    == product.supplier_id
                )
                .first()
            )

            if (
                owner is not None
                and owner
                not in matched_suppliers
            ):
                matched_suppliers.append(
                    owner
                )

        return (
            matched_suppliers,
            matched_products,
        )

    # =========================================================
    # SQL SUPPLY CHAIN LINKS
    # =========================================================

    def _create_supply_chain_links(
        self,
        event: Event,
        suppliers: list[Supplier],
        products: list[Product],
    ) -> list[int]:

        severity = str(
            event.severity
            or "medium"
        ).lower()

        impact_level = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }.get(
            severity,
            "medium",
        )

        estimated_delay = {
            "critical": 14.0,
            "high": 10.0,
            "medium": 7.0,
            "low": 3.0,
        }.get(
            severity,
            7.0,
        )

        created_links: list[int] = []

        for product in products:

            supplier_id = (
                product.supplier_id
            )

            if supplier_id is None:
                continue

            existing = (
                self.db.query(
                    SupplyChainLink
                )
                .filter(
                    SupplyChainLink.event_id
                    == event.id,

                    SupplyChainLink.product_id
                    == product.id,

                    SupplyChainLink.supplier_id
                    == supplier_id,
                )
                .first()
            )

            if existing is not None:
                continue

            link = SupplyChainLink(
                event_id=event.id,
                supplier_id=supplier_id,
                product_id=product.id,
                relationship_type="affected",
                impact_level=impact_level,
                estimated_delay_days=estimated_delay,
            )

            self.db.add(link)
            self.db.flush()

            created_links.append(
                link.id
            )

        self.db.commit()

        return created_links

    # =========================================================
    # BUSINESS SUPPLY-CHAIN SIMULATION
    # =========================================================

    def _simulate_business_impact(
        self,
        matched_business_suppliers: list[
            dict[str, Any]
        ],
        event_location: str | None = None,
        event_severity: str | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the business simulation using the actual event
        context.

        Event context is intentionally passed all the way down:

            news
              ↓
            location
            severity
            event type
              ↓
            route intelligence
              ↓
            supplier simulation

        This is what makes the simulation event-aware rather
        than being a generic supplier-failure calculation.
        """

        if not matched_business_suppliers:

            return {
                "success": False,
                "status": "supplier_not_resolved",
                "message": (
                    "No business supply-chain supplier "
                    "could be resolved from the news."
                ),
                "suppliers": [],
                "simulations": [],
            }

        simulator = (
            DisruptionSimulator(
                self.db,
                user_id=self.user_id,
            )
        )

        simulations: list[
            dict[str, Any]
        ] = []

        for supplier in (
            matched_business_suppliers
        ):

            supplier_id = str(
                supplier[
                    "supplier_id"
                ]
            )

            try:

                simulation = (
                    simulator
                    .simulate_supplier_failure(
                        supplier_id=(
                            supplier_id
                        ),
                        disruption_location=(
                            event_location
                        ),
                        severity=(
                            event_severity
                        ),
                        event_type=(
                            event_type
                        ),
                    )
                )

                simulations.append(
                    {
                        "supplier": supplier,
                        "simulation": simulation,
                    }
                )

            except Exception as exc:

                simulations.append(
                    {
                        "supplier": supplier,
                        "simulation": {
                            "success": False,
                            "error": str(
                                exc
                            ),
                        },
                    }
                )

        successful = [
            item
            for item in simulations
            if item["simulation"].get(
                "success"
            )
        ]

        return {
            "success": bool(
                successful
            ),

            "status": (
                "simulated"
                if successful
                else "simulation_failed"
            ),

            "event_context": {
                "location": event_location,
                "severity": event_severity,
                "event_type": event_type,
            },

            "suppliers": (
                matched_business_suppliers
            ),

            "simulations": simulations,
        }

    # =========================================================
    # NEO4J EVENT GRAPH
    # =========================================================

    def _sync_event_graph(
        self,
        event: Event,
        matched_suppliers: list[Supplier],
        matched_products: list[Product],
        impact_level: str,
        estimated_delay: float,
    ) -> dict[str, Any]:

        try:

            self.neo4j.create_event(
                event_id=event.id,
                title=event.title,
                event_type=event.event_type,
                severity=event.severity,
                location=event.location,
            )

            for supplier in (
                matched_suppliers
            ):

                self.neo4j.create_supplier(
                    supplier_id=supplier.id,
                    name=supplier.name,
                    country=supplier.country,
                    industry=supplier.industry,
                )

            for product in (
                matched_products
            ):

                self.neo4j.create_product(
                    product_id=product.id,
                    name=product.name,
                    category=product.category,
                )

            for supplier in (
                matched_suppliers
            ):

                self.neo4j.create_event_supplier_relationship(
                    event_id=event.id,
                    supplier_id=supplier.id,
                    relationship_type="affected",
                    impact_level=impact_level,
                    estimated_delay_days=estimated_delay,
                )

            for product in (
                matched_products
            ):

                if product.supplier_id is None:
                    continue

                owner = (
                    self.db.query(
                        Supplier
                    )
                    .filter(
                        Supplier.id
                        == product.supplier_id
                    )
                    .first()
                )

                if owner is None:
                    continue

                self.neo4j.create_supplier_product_relationship(
                    supplier_id=owner.id,
                    product_id=product.id,
                )

            return {
                "success": True,
            }

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc),
            }

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
    # AGGREGATE BUSINESS IMPACT
    # =========================================================

    @staticmethod
    def _aggregate_business_impact(
        business_impact: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Aggregate all successful supplier simulations into one
        business-level impact summary.

        Important route semantics:

            normal_transit_days
                = normal route transit time.

            additional_disruption_delay_days
                = delay introduced by the event.

            effective_route_time_days
                = normal transit + additional disruption delay.

        Normal transit is NEVER counted as disruption delay.

        The simulator is the source of truth for component-level
        impact. This method only aggregates those values and does
        not invent missing route information.
        """

        if not isinstance(
            business_impact,
            dict,
        ):
            return IntelligencePipeline._empty_business_summary()

        simulations = business_impact.get(
            "simulations",
            [],
        )

        if not isinstance(
            simulations,
            list,
        ):
            simulations = []

        total_lost_supply = 0.0
        total_alternative_recovery = 0.0
        total_gross_shortage = 0.0
        total_net_shortage = 0.0

        max_risk = 0.0
        max_delay = 0.0

        max_normal_transit = 0.0
        max_disruption_delay = 0.0
        max_effective_route_time = 0.0

        production_stop = False

        affected_components = 0
        affected_products = 0
        affected_plants = 0

        products_buffered = 0
        products_route_delayed = 0
        products_with_shortage = 0

        successful_count = 0

        for item in simulations:

            if not isinstance(
                item,
                dict,
            ):
                continue

            # -------------------------------------------------
            # Support the canonical nested format:
            #
            # {
            #     "supplier": {...},
            #     "simulation": {
            #         "success": True,
            #         ...
            #     }
            # }
            #
            # Also support the historical flat format where
            # simulation fields were placed directly on item.
            # -------------------------------------------------

            simulation = item.get(
                "simulation",
            )

            if not isinstance(
                simulation,
                dict,
            ):
                simulation = item

            if not simulation.get(
                "success",
                False,
            ):
                continue

            successful_count += 1

            summary = simulation.get(
                "summary",
                {},
            )

            if not isinstance(
                summary,
                dict,
            ):
                summary = {}

            components = simulation.get(
                "components",
                [],
            )

            if not isinstance(
                components,
                list,
            ):
                components = []

            products = simulation.get(
                "products",
                [],
            )

            if not isinstance(
                products,
                list,
            ):
                products = []

            plants = simulation.get(
                "plants",
                [],
            )

            if not isinstance(
                plants,
                list,
            ):
                plants = []

            # -------------------------------------------------
            # Primary business totals.
            #
            # Prefer simulator summary because it already
            # represents the complete supplier simulation.
            # -------------------------------------------------

            total_lost_supply += (
                IntelligencePipeline._number(
                    summary.get(
                        "gross_lost_supply",
                        0,
                    )
                )
            )

            total_alternative_recovery += (
                IntelligencePipeline._number(
                    summary.get(
                        "alternative_recovery",
                        0,
                    )
                )
            )

            total_gross_shortage += (
                IntelligencePipeline._number(
                    summary.get(
                        "gross_shortage",
                        0,
                    )
                )
            )

            total_net_shortage += (
                IntelligencePipeline._number(
                    summary.get(
                        "net_shortage",
                        0,
                    )
                )
            )

            max_risk = max(
                max_risk,
                IntelligencePipeline._number(
                    summary.get(
                        "max_risk_score",
                        summary.get(
                            "max_risk",
                            0,
                        ),
                    )
                ),
            )

            max_delay = max(
                max_delay,
                IntelligencePipeline._number(
                    summary.get(
                        "max_delay_days",
                        0,
                    )
                ),
            )

            production_stop = (
                production_stop
                or bool(
                    summary.get(
                        "production_stop",
                        False,
                    )
                )
            )

            # -------------------------------------------------
            # Counts.
            #
            # Prefer simulator summary counts, because product
            # and plant impact may contain multiple records.
            # -------------------------------------------------

            affected_components += int(
                IntelligencePipeline._number(
                    summary.get(
                        "affected_components",
                        len(components),
                    )
                )
            )

            affected_products += int(
                IntelligencePipeline._number(
                    summary.get(
                        "affected_products",
                        len(products),
                    )
                )
            )

            affected_plants += int(
                IntelligencePipeline._number(
                    summary.get(
                        "affected_plants",
                        len(plants),
                    )
                )
            )

            products_buffered += int(
                IntelligencePipeline._number(
                    summary.get(
                        "products_buffered",
                        0,
                    )
                )
            )

            products_route_delayed += int(
                IntelligencePipeline._number(
                    summary.get(
                        "products_route_delayed",
                        0,
                    )
                )
            )

            products_with_shortage += int(
                IntelligencePipeline._number(
                    summary.get(
                        "products_with_shortage",
                        0,
                    )
                )
            )

            # -------------------------------------------------
            # ROUTE AGGREGATION
            #
            # Component records are the authoritative source for
            # route timing.
            #
            # Do NOT use normal transit as disruption delay.
            # -------------------------------------------------

            for component in components:

                if not isinstance(
                    component,
                    dict,
                ):
                    continue

                normal_transit = (
                    IntelligencePipeline._number(
                        component.get(
                            "route_transit_days",
                            component.get(
                                "normal_transit_days",
                                0,
                            ),
                        )
                    )
                )

                disruption_delay = (
                    IntelligencePipeline._number(
                        component.get(
                            "route_disruption_delay_days",
                            component.get(
                                "additional_disruption_delay_days",
                                0,
                            ),
                        )
                    )
                )

                effective_route_time = (
                    IntelligencePipeline._number(
                        component.get(
                            "effective_route_time_days",
                            0,
                        )
                    )
                )

                # If an older component payload has no explicit
                # effective value but has both timing pieces,
                # derive it safely.
                if (
                    effective_route_time <= 0
                    and normal_transit > 0
                ):
                    effective_route_time = (
                        normal_transit
                        + disruption_delay
                    )

                max_normal_transit = max(
                    max_normal_transit,
                    normal_transit,
                )

                max_disruption_delay = max(
                    max_disruption_delay,
                    disruption_delay,
                )

                max_effective_route_time = max(
                    max_effective_route_time,
                    effective_route_time,
                )

            # -------------------------------------------------
            # Product-level fallback.
            #
            # This is only used for counts when simulator summary
            # does not provide them.
            # -------------------------------------------------

            if "products_buffered" not in summary:
                products_buffered += sum(
                    1
                    for product in products
                    if isinstance(
                        product,
                        dict,
                    )
                    and product.get(
                        "exposure_status"
                    ) == "buffered"
                )

            if "products_route_delayed" not in summary:
                products_route_delayed += sum(
                    1
                    for product in products
                    if isinstance(
                        product,
                        dict,
                    )
                    and product.get(
                        "exposure_status"
                    ) == "route_delayed"
                )

            if "products_with_shortage" not in summary:
                products_with_shortage += sum(
                    1
                    for product in products
                    if isinstance(
                        product,
                        dict,
                    )
                    and product.get(
                        "exposure_status"
                    ) == "shortage"
                )

        if successful_count == 0:
            return IntelligencePipeline._empty_business_summary()

        return {
            "affected_components": (
                affected_components
            ),

            "affected_products": (
                affected_products
            ),

            "affected_plants": (
                affected_plants
            ),

            "gross_lost_supply": round(
                total_lost_supply,
                2,
            ),

            "alternative_recovery": round(
                total_alternative_recovery,
                2,
            ),

            "gross_shortage": round(
                total_gross_shortage,
                2,
            ),

            "net_shortage": round(
                total_net_shortage,
                2,
            ),

            # -----------------------------------------------
            # Route intelligence.
            # -----------------------------------------------

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

            "max_delay_days": round(
                max_delay,
                2,
            ),

            "max_route_disruption_delay_days": round(
                max_disruption_delay,
                2,
            ),

            "max_risk_score": round(
                max_risk,
                2,
            ),

            # Backward-compatible alias.
            "max_risk": round(
                max_risk,
                2,
            ),

            "production_stop": (
                production_stop
            ),

            "products_buffered": (
                products_buffered
            ),

            "products_route_delayed": (
                products_route_delayed
            ),

            "products_with_shortage": (
                products_with_shortage
            ),
        }

    # =========================================================
    # EMPTY BUSINESS SUMMARY
    # =========================================================

    @staticmethod
    def _empty_business_summary() -> dict[str, Any]:
        """
        Canonical empty business summary.

        Zero means no measured impact.
        It does not mean unknown route data was inferred.
        """

        return {
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
            "max_risk": 0.0,

            "production_stop": False,

            "products_buffered": 0,
            "products_route_delayed": 0,
            "products_with_shortage": 0,
        }

    # =========================================================
    # MAIN PIPELINE
    # =========================================================

    def process(
        self,
        title: str,
        description: str,
        source: str = "manual",
        auto_simulate: bool = True,
    ) -> dict[str, Any]:

        title = title.strip()
        description = description.strip()

        if not title:
            raise ValueError(
                "News title is required."
            )

        if not description:
            raise ValueError(
                "News description is required."
            )

        # =====================================================
        # 1. NLP
        # =====================================================

        nlp_result = nlp_engine.analyze(
            title=title,
            description=description,
        )

        # =====================================================
        # 2. CREATE SQL EVENT
        # =====================================================

        locations = nlp_result.get(
            "locations",
            [],
        )

        location_candidates = [
            str(location).strip()
            for location in locations
            if str(location).strip()
        ]

        resolved_locations = [
            LocationResolutionService.resolve(
                location
            )
            for location in location_candidates
        ]

        # Prefer:
        #   port > city > country > unknown
        #
        # Never invent a location.
        location_priority = {
            "port": 3,
            "city": 2,
            "country": 1,
            "unknown": 0,
        }

        resolved_locations.sort(
            key=lambda item: (
                -location_priority.get(
                    item.get(
                        "location_type",
                        "unknown",
                    ),
                    0,
                ),
                -float(
                    item.get(
                        "confidence",
                        0.0,
                    )
                ),
            )
        )

        primary_location = (
            resolved_locations[0]
            if resolved_locations
            else {
                "raw": None,
                "normalized": None,
                "location_type": "unknown",
                "city": None,
                "country": None,
                "confidence": 0.0,
                "match_reasons": [],
            }
        )

        location = (
            primary_location.get(
                "city"
            )
            or primary_location.get(
                "country"
            )
            or primary_location.get(
                "raw"
            )
        )

        severity = str(
            nlp_result.get(
                "severity",
                "medium",
            )
        ).lower()

        event_type = str(
            nlp_result.get(
                "event_type",
                "supply_chain_disruption",
            )
        )

        from app.models.business_supply_chain import Company
        co_q = self.db.query(Company)
        if self.user_id is not None:
            co_q = co_q.filter(Company.user_id == self.user_id)
        active_co = co_q.first()
        active_cid = active_co.company_id if active_co else None

        event = Event(
            title=nlp_result.get(
                "title",
                title,
            ),
            description=nlp_result.get(
                "description",
                description,
            ),
            source=source or "manual",
            event_type=event_type,
            location=location,
            severity=severity,
            status="active",
            company_id=active_cid,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # =====================================================
        # 3. LEGACY CANONICAL MATCHING
        # =====================================================

        (
            matched_suppliers,
            matched_products,
        ) = self._match_legacy_entities(
            title=title,
            description=description,
            nlp_result=nlp_result,
        )

        # =====================================================
        # 4. BUSINESS SUPPLIER MATCHING
        # =====================================================

        business_supplier_matches = (
            self._match_business_suppliers(
                title=title,
                description=description,
                nlp_result=nlp_result,
            )
        )

        # =====================================================
        # 5. SQL SUPPLY-CHAIN LINKS
        # =====================================================

        created_links = (
            self._create_supply_chain_links(
                event=event,
                suppliers=matched_suppliers,
                products=matched_products,
            )
        )

        # =====================================================
        # 6. NEO4J EVENT GRAPH
        # =====================================================

        impact_level = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }.get(
            severity,
            "medium",
        )

        estimated_delay = {
            "critical": 14.0,
            "high": 10.0,
            "medium": 7.0,
            "low": 3.0,
        }.get(
            severity,
            7.0,
        )

        neo4j_result = (
            self._sync_event_graph(
                event=event,
                matched_suppliers=matched_suppliers,
                matched_products=matched_products,
                impact_level=impact_level,
                estimated_delay=estimated_delay,
            )
        )

        # =====================================================
        # 7. PREDICTION
        # =====================================================
        #
        # Keep the legacy business prediction as the base signal,
        # then add the GNN-backed hybrid prediction.
        #
        # Business simulation remains authoritative for business
        # impact. GNN/hybrid remains a separate predictive signal.
        #
        # Canonical graph ID:
        #
        #     event_48
        #
        # This is the same ID used by Neo4j and GNNGraphService.
        # =====================================================

        prediction: Any = None

        try:

            base_prediction = (
                predict_event_impact(
                    self.db,
                    event.id,
                )
            )

            if not isinstance(
                base_prediction,
                dict,
            ):
                base_prediction = {
                    "success": False,
                    "error": (
                        "Legacy prediction returned "
                        "an invalid response."
                    ),
                }

            prediction = dict(
                base_prediction
            )

            graph_id = (
                f"event_{event.id}"
            )

            try:

                hybrid_service = (
                    HybridPredictionService()
                )

                hybrid_prediction = (
                    hybrid_service.predict(
                        db=self.db,
                        event_id=event.id,
                        graph_id=graph_id,
                    )
                )

                prediction[
                    "hybrid_prediction"
                ] = (
                    hybrid_prediction.get(
                        "hybrid_prediction"
                    )
                    if isinstance(
                        hybrid_prediction,
                        dict,
                    )
                    else None
                )

                if isinstance(
                    hybrid_prediction,
                    dict,
                ):

                    prediction[
                        "gnn_prediction"
                    ] = (
                        hybrid_prediction.get(
                            "gnn_prediction"
                        )
                    )

                    prediction[
                        "hybrid_prediction"
                    ] = (
                        hybrid_prediction.get(
                            "hybrid_prediction"
                        )
                    )

                    prediction[
                        "weights"
                    ] = (
                        hybrid_prediction.get(
                            "weights"
                        )
                    )

                    prediction[
                        "hybrid_success"
                    ] = bool(
                        hybrid_prediction.get(
                            "success"
                        )
                    )

                    if not hybrid_prediction.get(
                        "success"
                    ):

                        prediction[
                            "hybrid_error"
                        ] = (
                            hybrid_prediction.get(
                                "error",
                                "Hybrid prediction failed.",
                            )
                        )

                # HybridPredictionService owns its own Neo4j
                # connection. Close it after inference.
                try:

                    hybrid_service.neo4j.close()

                except Exception:

                    pass

            except Exception as exc:

                # Prediction must not break the business
                # intelligence pipeline if ML inference fails.
                prediction[
                    "hybrid_prediction"
                ] = None

                prediction[
                    "gnn_prediction"
                ] = None

                prediction[
                    "hybrid_success"
                ] = False

                prediction[
                    "hybrid_error"
                ] = str(
                    exc
                )

        except Exception as exc:

            prediction = {
                "success": False,
                "error": str(
                    exc
                ),
                "hybrid_prediction": None,
                "gnn_prediction": None,
                "hybrid_success": False,
                "hybrid_error": (
                    "Hybrid prediction was not "
                    "executed because the base "
                    "prediction failed."
                ),
            }

        # =====================================================
        # 8. BUSINESS IMPACT SIMULATION
        # =====================================================

        business_impact = {
            "success": False,
            "status": "not_requested",
            "message": (
                "Automatic business simulation "
                "was disabled."
            ),
            "suppliers": [],
            "simulations": [],
        }

        if auto_simulate:

            business_impact = (
                self._simulate_business_impact(
                    matched_business_suppliers=(
                        business_supplier_matches
                    ),
                    event_location=(
                        event.location
                    ),
                    event_severity=(
                        event.severity
                    ),
                    event_type=(
                        event.event_type
                    ),
                )
            )

        # =====================================================
        # 9. AGGREGATED IMPACT
        # =====================================================

        business_summary = (
            self._aggregate_business_impact(
                business_impact
            )
        )

        # =====================================================
        # 10. GRAPH ID
        # =====================================================

        graph_id = (
            f"event_{event.id}"
        )

        # =====================================================
        # 11. FINAL RESPONSE
        # =====================================================

        return {
            "success": True,

            "event_id": event.id,

            "graph_id": graph_id,

            "message": (
                "News analyzed and mapped against "
                "the AtmoGraph supply chain."
            ),

            "event": {
                "id": event.id,
                "event_id": event.id,
                "title": event.title,
                "description": event.description,
                "source": event.source,
                "event_type": event.event_type,
                "location": event.location,
                "severity": event.severity,
                "status": event.status,

                "location_resolution": {
                    "raw": primary_location.get(
                        "raw"
                    ),
                    "normalized": primary_location.get(
                        "normalized"
                    ),
                    "location_type": primary_location.get(
                        "location_type"
                    ),
                    "city": primary_location.get(
                        "city"
                    ),
                    "country": primary_location.get(
                        "country"
                    ),
                    "confidence": primary_location.get(
                        "confidence"
                    ),
                    "match_reasons": primary_location.get(
                        "match_reasons",
                        [],
                    ),
                },

                "location_candidates": (
                    resolved_locations
                ),
            },

            "nlp": nlp_result,

            "resolved": {
                "suppliers": [
                    {
                        "id": supplier.id,
                        "name": supplier.name,
                    }
                    for supplier
                    in matched_suppliers
                ],

                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "supplier_id": (
                            product.supplier_id
                        ),
                    }
                    for product
                    in matched_products
                ],
            },

            "business_supply_chain": {
                "matched_suppliers": (
                    business_supplier_matches
                ),

                "supplier_match_count": len(
                    business_supplier_matches
                ),

                "simulation": business_impact,

                "summary": business_summary,
            },

            "graph": {
                "success": True,

                "event_id": event.id,

                "graph_id": graph_id,

                "suppliers": len(
                    matched_suppliers
                ),

                "products": len(
                    matched_products
                ),

                "created_links": len(
                    created_links
                ),
            },

            "neo4j": neo4j_result,

            "prediction": prediction,
        }


__all__ = [
    "IntelligencePipeline",
]