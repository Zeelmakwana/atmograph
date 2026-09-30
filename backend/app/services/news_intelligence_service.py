from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.supply_chain import Supplier, Product
from app.models.supply_chain_link import SupplyChainLink

from app.services.nlp_engine import nlp_engine
from app.services.neo4j_service import Neo4jService
from app.services.entity_graph_builder import EntityGraphBuilder
from app.services.hybrid_prediction_service import HybridPredictionService


class NewsIntelligenceService:

    def __init__(self) -> None:
        self.neo4j = Neo4jService()
        self.graph_builder = EntityGraphBuilder()
        self.hybrid_service = HybridPredictionService()

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(value: str) -> str:
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
    # IMPACT LEVEL
    # =========================================================

    @staticmethod
    def _impact_level(
        severity: str,
    ) -> str:

        severity = str(
            severity
        ).lower().strip()

        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }

        return mapping.get(
            severity,
            "medium",
        )

    # =========================================================
    # ESTIMATED DELAY
    # =========================================================

    @staticmethod
    def _estimated_delay(
        severity: str,
    ) -> int:

        severity = str(
            severity
        ).lower().strip()

        mapping = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1,
        }

        return mapping.get(
            severity,
            4,
        )

    # =========================================================
    # CANONICAL ENTITY RESOLUTION
    # =========================================================

    def _enrich_supply_chain_graph(
        self,
        db: Session,
        nodes: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        event_node_id: str,
    ) -> dict[str, Any]:

        suppliers = db.query(
            Supplier
        ).all()

        products = db.query(
            Product
        ).all()

        supplier_map = {
            self._normalize(s.name): s
            for s in suppliers
            if s.name
        }

        product_map = {
            self._normalize(p.name): p
            for p in products
            if p.name
        }

        # ---------------------------------------------------------
        # old NLP node ID → canonical node ID
        # ---------------------------------------------------------

        replacement_map: dict[str, str] = {}

        canonical_nodes: list[
            dict[str, Any]
        ] = []

        resolved_suppliers: dict[
            int,
            Supplier,
        ] = {}

        resolved_products: dict[
            int,
            Product,
        ] = {}

        # ---------------------------------------------------------
        # Resolve every NLP node
        # ---------------------------------------------------------

        for node in nodes:

            old_id = node["id"]

            name = str(
                node.get("name", "")
            ).strip()

            normalized = self._normalize(
                name
            )

            # =====================================================
            # SUPPLIER
            # =====================================================

            supplier = supplier_map.get(
                normalized
            )

            if supplier:

                canonical_id = (
                    f"supplier_{supplier.id}"
                )

                replacement_map[
                    old_id
                ] = canonical_id

                resolved_suppliers[
                    supplier.id
                ] = supplier

                if not any(
                    n["id"] == canonical_id
                    for n in canonical_nodes
                ):

                    canonical_nodes.append(
                        {
                            "id": canonical_id,
                            "label": "Supplier",
                            "name": supplier.name,
                            "properties": {
                                "supplier_id": supplier.id,
                                "canonical": True,
                                "source": "database_resolution",
                            },
                        }
                    )

                continue

            # =====================================================
            # PRODUCT
            # =====================================================

            product = product_map.get(
                normalized
            )

            if product:

                canonical_id = (
                    f"product_{product.id}"
                )

                replacement_map[
                    old_id
                ] = canonical_id

                resolved_products[
                    product.id
                ] = product

                if not any(
                    n["id"] == canonical_id
                    for n in canonical_nodes
                ):

                    canonical_nodes.append(
                        {
                            "id": canonical_id,
                            "label": "Product",
                            "name": product.name,
                            "properties": {
                                "product_id": product.id,
                                "supplier_id": product.supplier_id,
                                "canonical": True,
                                "source": "database_resolution",
                            },
                        }
                    )

                continue

            # =====================================================
            # UNKNOWN ENTITY
            # =====================================================

            canonical_nodes.append(
                node
            )

        # ---------------------------------------------------------
        # Keep Event + non-canonical nodes
        # ---------------------------------------------------------

        # ---------------------------------------------------------
        # Rebuild Event relationships
        # ---------------------------------------------------------

        updated_relationships: list[
            dict[str, Any]
        ] = []

        for rel in relationships:

            source = replacement_map.get(
                rel["source"],
                rel["source"],
            )

            target = replacement_map.get(
                rel["target"],
                rel["target"],
            )

            relationship_type = rel["type"]

            # Event → Supplier
            if (
                source == event_node_id
                and target.startswith("supplier_")
            ):
                relationship_type = "AFFECTS"

            # Event → Product
            elif (
                source == event_node_id
                and target.startswith("product_")
            ):
                relationship_type = "AFFECTS"

            updated = {
                "source": source,
                "target": target,
                "type": relationship_type,
            }

            if updated not in updated_relationships:
                updated_relationships.append(
                    updated
                )

        # ---------------------------------------------------------
        # Add Supplier → Product relationships
        # ---------------------------------------------------------

        for supplier in resolved_suppliers.values():

            supplier_id = (
                f"supplier_{supplier.id}"
            )

            for product in products:

                if product.supplier_id != supplier.id:
                    continue

                product_id = (
                    f"product_{product.id}"
                )

                if not any(
                    n["id"] == product_id
                    for n in canonical_nodes
                ):

                    canonical_nodes.append(
                        {
                            "id": product_id,
                            "label": "Product",
                            "name": product.name,
                            "properties": {
                                "product_id": product.id,
                                "supplier_id": supplier.id,
                                "canonical": True,
                                "source": "database",
                            },
                        }
                    )

                relationship = {
                    "source": supplier_id,
                    "target": product_id,
                    "type": "SUPPLIES",
                }

                if relationship not in updated_relationships:
                    updated_relationships.append(
                        relationship
                    )

                resolved_products[
                    product.id
                ] = product

        # ---------------------------------------------------------
        # Replace graph lists
        # ---------------------------------------------------------

        nodes.clear()
        nodes.extend(
            canonical_nodes
        )

        relationships.clear()
        relationships.extend(
            updated_relationships
        )

        return {
            "suppliers": list(
                resolved_suppliers.values()
            ),
            "products": list(
                resolved_products.values()
            ),
        }

    # =========================================================
    # POSTGRES SUPPLY-CHAIN LINKS
    # =========================================================

    def _create_supply_chain_links(
        self,
        db: Session,
        event: Event,
        suppliers: list[Supplier],
        products: list[Product],
    ) -> None:

        impact_level = self._impact_level(
            event.severity
        )

        delay_days = self._estimated_delay(
            event.severity
        )

        # ---------------------------------------------------------
        # Create one link per affected supplier/product
        # ---------------------------------------------------------

        for supplier in suppliers:

            supplier_products = [
                p
                for p in products
                if p.supplier_id == supplier.id
            ]

            # If no product was explicitly resolved,
            # use all products supplied by this supplier.
            if not supplier_products:

                supplier_products = [
                    p
                    for p in db.query(Product).all()
                    if p.supplier_id == supplier.id
                ]

            for product in supplier_products:

                existing = (
                    db.query(
                        SupplyChainLink
                    )
                    .filter(
                        SupplyChainLink.event_id
                        == event.id,
                        SupplyChainLink.supplier_id
                        == supplier.id,
                        SupplyChainLink.product_id
                        == product.id,
                    )
                    .first()
                )

                if existing:
                    continue

                link = SupplyChainLink(
                    event_id=event.id,
                    supplier_id=supplier.id,
                    product_id=product.id,
                    relationship_type="affected",
                    impact_level=impact_level,
                    estimated_delay_days=delay_days,
                )

                db.add(link)

        db.commit()

    # =========================================================
    # MAIN PIPELINE
    # =========================================================

    def analyze_and_create_event(
        self,
        db: Session,
        title: str,
        description: str,
        source: str | None = None,
    ) -> dict:

        # ---------------------------------------------------------
        # 1. NLP
        # ---------------------------------------------------------

        nlp_result = nlp_engine.analyze(
            title,
            description,
        )

        # ---------------------------------------------------------
        # 2. BUILD INITIAL NLP GRAPH
        # ---------------------------------------------------------

        graph_result = (
            self.graph_builder.build(
                nlp_result
            )
        )

        nodes = graph_result.get(
            "nodes",
            [],
        )

        relationships = graph_result.get(
            "relationships",
            [],
        )

        event_node = next(
            (
                node
                for node in nodes
                if node.get("label") == "Event"
            ),
            None,
        )

        if event_node is None:
            raise ValueError(
                "NLP graph did not produce an Event node."
            )

        event_node_id = event_node[
            "id"
        ]

        # ---------------------------------------------------------
        # 3. CREATE POSTGRES EVENT
        # ---------------------------------------------------------

        event = Event(
            title=title,
            description=description,
            source=source
            or "NLP News Intelligence",
            event_type=nlp_result.get(
                "event_type",
                "supply_chain_disruption",
            ),
            location=nlp_result.get(
                "location"
            ),
            severity=nlp_result.get(
                "severity",
                "medium",
            ),
            status="active",
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        graph_id = (
            f"event_{event.id}"
        )

        # ---------------------------------------------------------
        # 4. GRAPH ID
        # ---------------------------------------------------------

        event_node["graph_id"] = graph_id
        event_node["event_id"] = event.id

        # ---------------------------------------------------------
        # 5. CANONICAL RESOLUTION
        # ---------------------------------------------------------

        resolution = (
            self._enrich_supply_chain_graph(
                db=db,
                nodes=nodes,
                relationships=relationships,
                event_node_id=event_node_id,
            )
        )

        suppliers = resolution[
            "suppliers"
        ]

        products = resolution[
            "products"
        ]

        # ---------------------------------------------------------
        # 6. POSTGRES SUPPLY-CHAIN LINKS
        # ---------------------------------------------------------

        self._create_supply_chain_links(
            db=db,
            event=event,
            suppliers=suppliers,
            products=products,
        )

        # ---------------------------------------------------------
        # 7. NEO4J
        # ---------------------------------------------------------

        neo4j_result = (
            self.neo4j.sync_nlp_graph(
                nodes=nodes,
                relationships=relationships,
            )
        )

        # ---------------------------------------------------------
        # 8. HYBRID PREDICTION
        # ---------------------------------------------------------

        prediction_result = (
            self.hybrid_service.predict(
                db=db,
                event_id=event.id,
                graph_id=graph_id,
            )
        )

        # ---------------------------------------------------------
        # 9. RESPONSE
        # ---------------------------------------------------------

        return {
            "success": True,
            "event_id": event.id,
            "graph_id": graph_id,

            "message": (
                "News analyzed, canonical entities resolved, "
                "supply-chain links created, graph synchronized, "
                "and hybrid prediction generated."
            ),

            "nlp": nlp_result,

            "graph": {
                "nodes": nodes,
                "relationships": relationships,
            },

            "neo4j": neo4j_result,

            "prediction": prediction_result,
        }