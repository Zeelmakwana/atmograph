"""
AtmoGraph Neo4j Graph Intelligence Service.

This service is responsible for the Neo4j knowledge graph used by
AtmoGraph for supply-chain relationship analysis.

Canonical Graph:

Event
   │
   ├── AFFECTS ──> Supplier
   │                  │
   │                  └── SUPPLIES ──> Product
   │
   └── AFFECTS ──> Product

The service also supports NLP-generated graphs.

Important:
NLP nodes can have temporary IDs such as:

    event_global_components_ltd_faces_critical_production_disruption

while the canonical Event node uses:

    event_18

This service normalizes those IDs before creating relationships.
"""

from __future__ import annotations

import os
import re
from typing import Any

from neo4j import GraphDatabase


class Neo4jService:
    """Central Neo4j service for AtmoGraph."""

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:

        self.uri = uri or os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687",
        )

        self.username = username or os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )

        self.password = password or os.getenv(
            "NEO4J_PASSWORD",
            "password",
        )

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(
                    self.username,
                    self.password,
                ),
            )
        except Exception as e:
            print(f"Warning: Could not initialize Neo4j driver: {e}")
            self.driver = None

    # =========================================================
    # CONNECTION
    # =========================================================

    def verify_connection(self) -> bool:
        """Verify that Neo4j is reachable."""

        try:
            self.driver.verify_connectivity()
            return True

        except Exception:
            return False

    def close(self) -> None:
        """Close Neo4j driver."""

        self.driver.close()

    # =========================================================
    # GENERIC QUERY
    # =========================================================

    def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query."""

        if self.driver is None:
            return []

        parameters = parameters or {}

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    parameters,
                )
                return [
                    record.data()
                    for record in result
                ]
        except Exception as e:
            print(f"Neo4j query error: {e}")
            return []

    # =========================================================
    # NODES
    # =========================================================

    def create_event(
        self,
        event_id: int,
        title: str,
        event_type: str,
        severity: str,
        location: str | None = None,
    ) -> None:
        """Create or update a canonical Event node."""

        graph_id = f"event_{event_id}"

        query = """
        MERGE (e:Event {event_id: $event_id})

        SET
            e.graph_id = $graph_id,
            e.title = $title,
            e.name = $title,
            e.event_type = $event_type,
            e.severity = $severity,
            e.location = $location
        """

        self.execute_query(
            query,
            {
                "event_id": event_id,
                "graph_id": graph_id,
                "title": title,
                "event_type": event_type,
                "severity": severity,
                "location": location,
            },
        )

    def create_supplier(
        self,
        supplier_id: int,
        name: str,
        country: str | None = None,
        industry: str | None = None,
    ) -> None:
        """Create or update a canonical Supplier node."""

        graph_id = f"supplier_{supplier_id}"

        query = """
        MERGE (s:Supplier {supplier_id: $supplier_id})

        SET
            s.graph_id = $graph_id,
            s.name = $name,
            s.country = $country,
            s.industry = $industry
        """

        self.execute_query(
            query,
            {
                "supplier_id": supplier_id,
                "graph_id": graph_id,
                "name": name,
                "country": country,
                "industry": industry,
            },
        )

    def create_product(
        self,
        product_id: int,
        name: str,
        category: str | None = None,
    ) -> None:
        """Create or update a canonical Product node."""

        graph_id = f"product_{product_id}"

        query = """
        MERGE (p:Product {product_id: $product_id})

        SET
            p.graph_id = $graph_id,
            p.name = $name,
            p.category = $category
        """

        self.execute_query(
            query,
            {
                "product_id": product_id,
                "graph_id": graph_id,
                "name": name,
                "category": category,
            },
        )

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    def create_event_supplier_relationship(
        self,
        event_id: int,
        supplier_id: int,
        relationship_type: str,
        impact_level: str,
        estimated_delay_days: float | None = None,
    ) -> None:
        """Create Event → Supplier relationship."""

        query = """
        MATCH (e:Event {event_id: $event_id})
        MATCH (s:Supplier {supplier_id: $supplier_id})

        MERGE (e)-[r:AFFECTS]->(s)

        SET
            r.relationship_type = $relationship_type,
            r.impact_level = $impact_level,
            r.estimated_delay_days = $estimated_delay_days
        """

        self.execute_query(
            query,
            {
                "event_id": event_id,
                "supplier_id": supplier_id,
                "relationship_type": relationship_type,
                "impact_level": impact_level,
                "estimated_delay_days": estimated_delay_days,
            },
        )

    def create_supplier_product_relationship(
        self,
        supplier_id: int,
        product_id: int,
    ) -> None:
        """Create Supplier → Product relationship."""

        query = """
        MATCH (s:Supplier {supplier_id: $supplier_id})
        MATCH (p:Product {product_id: $product_id})

        MERGE (s)-[:SUPPLIES]->(p)
        """

        self.execute_query(
            query,
            {
                "supplier_id": supplier_id,
                "product_id": product_id,
            },
        )

    # =========================================================
    # GRAPH STATISTICS
    # =========================================================

    def get_graph_statistics(self) -> dict[str, Any]:
        """Return high-level graph statistics."""

        query = """
        MATCH (n)
        WITH count(n) AS total_nodes

        OPTIONAL MATCH ()-[r]->()

        RETURN
            total_nodes,
            count(r) AS total_relationships
        """

        result = self.execute_query(query)

        if not result:
            return {
                "total_nodes": 0,
                "total_relationships": 0,
            }

        return result[0]

    # =========================================================
    # EVENT GRAPH
    # =========================================================

    def get_event_graph(
        self,
        event_id: int,
        max_depth: int = 4,
    ) -> list[dict[str, Any]]:
        """Return graph paths connected to a canonical event."""

        depth = max(
            1,
            min(max_depth, 6),
        )

        query = f"""
        MATCH path =
            (e:Event {{event_id: $event_id}})
            -[*1..{depth}]-
            (connected)

        RETURN path
        """

        return self.execute_query(
            query,
            {
                "event_id": event_id,
            },
        )

    # =========================================================
    # AFFECTED SUPPLIERS
    # =========================================================

    def get_affected_suppliers(
        self,
        event_id: int,
    ) -> list[dict[str, Any]]:
        """Return suppliers directly affected by an event."""

        query = """
        MATCH (e:Event {event_id: $event_id})
              -[r:AFFECTS]->
              (s:Supplier)

        WITH
            s.supplier_id AS supplier_id,
            s.name AS name,
            s.country AS country,
            s.industry AS industry,
            r.impact_level AS impact_level,
            r.estimated_delay_days AS estimated_delay_days

        RETURN DISTINCT
            supplier_id,
            name,
            country,
            industry,
            impact_level,
            estimated_delay_days

        ORDER BY supplier_id
        """

        return self.execute_query(
            query,
            {
                "event_id": event_id,
            },
        )

    # =========================================================
    # AFFECTED PRODUCTS
    # =========================================================

    def get_affected_products(
        self,
        event_id: int,
    ) -> list[dict[str, Any]]:
        """Return products affected through suppliers."""

        query = """
        MATCH (e:Event {event_id: $event_id})
              -[:AFFECTS]->
              (s:Supplier)
              -[:SUPPLIES]->
              (p:Product)

        RETURN DISTINCT
            p.product_id AS product_id,
            p.name AS name,
            p.category AS category,
            s.supplier_id AS supplier_id,
            s.name AS supplier_name
        """

        return self.execute_query(
            query,
            {
                "event_id": event_id,
            },
        )

    # =========================================================
    # RIPPLE PATHS
    # =========================================================

    def get_ripple_paths(
        self,
        event_id: int,
        max_depth: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find downstream ripple paths from an event.

        Example:

        Event
          ↓
        Supplier
          ↓
        Product
        """

        depth = max(
            1,
            min(max_depth, 6),
        )

        query = f"""
        MATCH path =
            (e:Event {{event_id: $event_id}})
            -[*1..{depth}]->
            (downstream)

        RETURN path
        """

        return self.execute_query(
            query,
            {
                "event_id": event_id,
            },
        )

    # =========================================================
    # EVENT DETAILS
    # =========================================================

    def get_event_details(
        self,
        event_id: int,
    ) -> list[dict[str, Any]]:
        """Return event node information."""

        query = """
        MATCH (e:Event {event_id: $event_id})

        RETURN
            e.event_id AS event_id,
            e.graph_id AS graph_id,
            e.title AS title,
            e.event_type AS event_type,
            e.severity AS severity,
            e.location AS location
        """

        return self.execute_query(
            query,
            {
                "event_id": event_id,
            },
        )

    # =========================================================
    # NLP → KNOWLEDGE GRAPH
    # =========================================================

    def sync_nlp_graph(
        self,
        nodes: list[dict],
        relationships: list[dict],
    ) -> dict:
        """
        Synchronize NLP/canonical graph data into Neo4j.

        Important ID normalization:

        NLP may produce:

            event_global_components_ltd_faces_critical_production_disruption

        while the canonical database event is:

            event_18

        Relationships are normalized through an ID map before
        being created.

        Canonical Supplier/Product nodes are NEVER deleted during
        synchronization because they can be shared by multiple
        events.
        """

        if self.driver is None:
            return {
                "success": False,
                "message": "Neo4j driver is not initialized.",
            }

        # ---------------------------------------------------------
        # Allowed Neo4j labels
        # ---------------------------------------------------------

        allowed_labels = {
            "Event",
            "Supplier",
            "Product",
            "Facility",
            "Location",
            "Person",
            "Group",
            "Entity",
            "Organization",
        }

        # ---------------------------------------------------------
        # Allowed relationship types
        # ---------------------------------------------------------

        allowed_relationships = {
            "OCCURS_AT",
            "INVOLVES",
            "AFFECTS",
            "RELATED_TO",
            "DISRUPTS",
            "IMPACTS",
            "SUPPLIES",
            "MANUFACTURES",
            "SHIPS_TO",
            "LOCATED_IN",
            "DEPENDS_ON",
            "DISTRIBUTES_TO",
        }

        # =========================================================
        # 1. BUILD NODE ID → CANONICAL GRAPH ID MAP
        # =========================================================

        id_map: dict[str, str] = {}

        prepared_nodes: list[dict[str, Any]] = []

        for node in nodes:

            node_id = str(
                node.get("id", "")
            ).strip()

            if not node_id:
                continue

            properties = node.get(
                "properties",
                {},
            )

            if not isinstance(properties, dict):
                properties = {}

            # Canonical graph_id may exist:
            #
            # 1. node["graph_id"]
            # 2. node["properties"]["graph_id"]
            # 3. node["id"]

            graph_id = str(
                node.get("graph_id")
                or properties.get("graph_id")
                or node_id
            ).strip()

            id_map[node_id] = graph_id

            label = node.get(
                "label",
                "Entity",
            )

            if label not in allowed_labels:
                label = "Entity"

            name = str(
                node.get(
                    "name",
                    properties.get(
                        "name",
                        graph_id,
                    ),
                )
            ).strip()

            prepared_nodes.append(
                {
                    "node_id": node_id,
                    "graph_id": graph_id,
                    "label": label,
                    "name": name,
                    "properties": properties,
                }
            )

        # =========================================================
        # 2. NORMALIZE RELATIONSHIPS
        # =========================================================

        normalized_relationships: list[dict[str, Any]] = []

        for relationship in relationships:

            raw_source = str(
                relationship.get("source", "")
            ).strip()

            raw_target = str(
                relationship.get("target", "")
            ).strip()

            if not raw_source or not raw_target:
                continue

            # Convert temporary NLP IDs to canonical graph IDs.
            source = id_map.get(
                raw_source,
                raw_source,
            )

            target = id_map.get(
                raw_target,
                raw_target,
            )

            relationship_type = str(
                relationship.get(
                    "type",
                    "RELATED_TO",
                )
            ).upper().strip()

            if relationship_type not in allowed_relationships:
                relationship_type = "RELATED_TO"

            properties = relationship.get(
                "properties",
                {},
            )

            if not isinstance(properties, dict):
                properties = {}

            normalized_relationships.append(
                {
                    "source": source,
                    "target": target,
                    "type": relationship_type,
                    "properties": properties,
                }
            )

        # =========================================================
        # 3. IDENTIFY CANONICAL EVENT IDS
        # =========================================================

        canonical_event_ids = []

        for node in prepared_nodes:

            if node["label"] == "Event":

                canonical_event_ids.append(
                    node["graph_id"]
                )

        canonical_event_ids = list(
            dict.fromkeys(
                canonical_event_ids
            )
        )

        # =========================================================
        # 4. IDENTIFY OLD TEMPORARY EVENT IDS
        # =========================================================

        temporary_event_ids = []

        for node in prepared_nodes:

            if node["label"] != "Event":
                continue

            node_id = node["node_id"]
            graph_id = node["graph_id"]

            if node_id != graph_id:
                temporary_event_ids.append(
                    node_id
                )

            # Also remove old stored graph_id if it was the
            # temporary NLP identifier.
            if graph_id != node_id:
                temporary_event_ids.append(
                    graph_id
                )

        temporary_event_ids = list(
            dict.fromkeys(
                temporary_event_ids
            )
        )

        # =========================================================
        # 5. WRITE GRAPH
        # =========================================================

        created_nodes = 0
        created_relationships = 0

        with self.driver.session() as session:

            # -----------------------------------------------------
            # Remove old temporary NLP Event nodes only.
            #
            # DO NOT delete Supplier/Product nodes because those
            # are canonical shared nodes.
            # -----------------------------------------------------

            if temporary_event_ids:

                session.run(
                    """
                    MATCH (e:Event)
                    WHERE e.graph_id IN $graph_ids
                    DETACH DELETE e
                    """,
                    graph_ids=temporary_event_ids,
                ).consume()

            # -----------------------------------------------------
            # Remove/recreate canonical Event nodes.
            #
            # This safely clears stale relationships attached to
            # the event while preserving Supplier/Product nodes.
            # -----------------------------------------------------

            if canonical_event_ids:

                session.run(
                    """
                    MATCH (e:Event)
                    WHERE e.graph_id IN $graph_ids
                    DETACH DELETE e
                    """,
                    graph_ids=canonical_event_ids,
                ).consume()

            # -----------------------------------------------------
            # CREATE / UPDATE NODES
            # -----------------------------------------------------

            for node in prepared_nodes:

                graph_id = node["graph_id"]
                label = node["label"]
                name = node["name"]
                properties = dict(
                    node["properties"]
                )

                # Never allow graph_id to be overwritten.
                properties.pop(
                    "graph_id",
                    None,
                )

                # -------------------------------------------------
                # Build safe common properties.
                # -------------------------------------------------

                query = f"""
                MERGE (n:{label} {{graph_id: $graph_id}})

                SET
                    n.name = $name

                SET n += $properties
                """

                session.run(
                    query,
                    graph_id=graph_id,
                    name=name,
                    properties=properties,
                ).consume()

                # -------------------------------------------------
                # Explicitly preserve canonical IDs.
                # -------------------------------------------------

                if "event_id" in properties:

                    session.run(
                        """
                        MATCH (n {graph_id: $graph_id})
                        SET n.event_id = $event_id
                        """,
                        graph_id=graph_id,
                        event_id=properties[
                            "event_id"
                        ],
                    ).consume()

                if "supplier_id" in properties:

                    session.run(
                        """
                        MATCH (n {graph_id: $graph_id})
                        SET n.supplier_id = $supplier_id
                        """,
                        graph_id=graph_id,
                        supplier_id=properties[
                            "supplier_id"
                        ],
                    ).consume()

                if "product_id" in properties:

                    session.run(
                        """
                        MATCH (n {graph_id: $graph_id})
                        SET n.product_id = $product_id
                        """,
                        graph_id=graph_id,
                        product_id=properties[
                            "product_id"
                        ],
                    ).consume()

                created_nodes += 1

            # -----------------------------------------------------
            # CREATE RELATIONSHIPS
            # -----------------------------------------------------

            for relationship in normalized_relationships:

                source = relationship["source"]
                target = relationship["target"]
                relationship_type = relationship["type"]
                properties = relationship["properties"]

                result = session.run(
                    f"""
                    MATCH (source {{graph_id: $source_id}})
                    MATCH (target {{graph_id: $target_id}})

                    MERGE (source)-[r:{relationship_type}]->(target)

                    SET r += $properties
                    """,
                    source_id=source,
                    target_id=target,
                    properties=properties,
                )

                summary = result.consume()

                created_relationships += (
                    summary.counters.relationships_created
                )

        # =========================================================
        # 6. VERIFY ACTUAL NEO4J GRAPH
        # =========================================================

        all_graph_ids = list(
            dict.fromkeys(
                [
                    node["graph_id"]
                    for node in prepared_nodes
                ]
            )
        )

        verification = self.execute_query(
            """
            MATCH (n)
            WHERE n.graph_id IN $graph_ids

            OPTIONAL MATCH (n)-[r]-(m)

            WHERE
                m.graph_id IN $graph_ids

            RETURN
                count(DISTINCT n) AS node_count,
                count(DISTINCT r) AS relationship_count
            """,
            {
                "graph_ids": all_graph_ids,
            },
        )

        final_node_count = 0
        final_relationship_count = 0

        if verification:

            final_node_count = int(
                verification[0].get(
                    "node_count",
                    0,
                )
            )

            final_relationship_count = int(
                verification[0].get(
                    "relationship_count",
                    0,
                )
            )

        # =========================================================
        # 7. RETURN DETAILED SYNC INFORMATION
        # =========================================================

        return {
            "success": True,
            "created_nodes": created_nodes,
            "created_relationships": created_relationships,
            "final_node_count": final_node_count,
            "final_relationship_count": final_relationship_count,
            "normalized_relationships": normalized_relationships,
        }

    # =========================================================
    # ENTITY NAME NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_entity_name(
        value: str,
    ) -> str:
        """
        Normalize entity names before matching.

        Examples:

        Global Components Ltd
        Global Components Ltd.
        GLOBAL COMPONENTS LTD
        Global   Components   Ltd

        all become the same normalized value.
        """

        value = str(
            value
        ).lower().strip()

        # Remove punctuation/special characters.
        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        # Normalize whitespace.
        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    # =========================================================
    # NLP EVENT RIPPLE ANALYSIS
    # =========================================================

    def get_nlp_ripple(
        self,
        graph_id: str,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Find downstream supply-chain ripple paths starting
        from an NLP-generated Event node.

        Example:

        Event
            ↓
        Supplier
            ↓
        Product
        """

        depth = max(
            1,
            min(max_depth, 5),
        )

        query = f"""
        MATCH path =
            (e:Event {{graph_id: $graph_id}})
            -[*1..{depth}]->
            (downstream)

        RETURN
            [node IN nodes(path) |
                {{
                    graph_id: node.graph_id,
                    label: labels(node),
                    name: node.name,
                    event_type: node.event_type,
                    severity: node.severity,
                    supplier_id: node.supplier_id,
                    product_id: node.product_id,
                    category: node.category
                }}
            ] AS nodes,

            [rel IN relationships(path) |
                {{
                    type: type(rel)
                }}
            ] AS relationships
        """

        return self.execute_query(
            query,
            {
                "graph_id": graph_id,
            },
        )


# =============================================================
# SHARED SERVICE INSTANCE
# =============================================================

neo4j_service = Neo4jService()