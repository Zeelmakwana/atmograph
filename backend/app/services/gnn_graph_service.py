from __future__ import annotations

from typing import Any

from app.services.neo4j_service import Neo4jService


class GNNGraphService:
    """
    Builds an event-centered graph from Neo4j and converts it
    into a GNN-ready representation.

    IMPORTANT:
    AtmoGraph uses graph_id as the stable application-level
    node identifier. We intentionally do NOT depend on Neo4j's
    internal elementId().
    """

    NODE_TYPES = {
        "Event": 0,
        "Supplier": 1,
        "Product": 2,
        "Facility": 3,
        "Location": 4,
        "Entity": 5,
        "Person": 6,
        "Group": 7,
        "Organization": 8,
    }

    RELATIONSHIP_TYPES = {
        "AFFECTS",
        "SUPPLIES",
        "OCCURS_AT",
        "INVOLVES",
        "RELATED_TO",
        "DISRUPTS",
        "IMPACTS",
        "MANUFACTURES",
        "SHIPS_TO",
        "LOCATED_IN",
        "DEPENDS_ON",
        "DISTRIBUTES_TO",
    }

    def __init__(self, neo4j: Neo4jService):
        self.neo4j = neo4j

    # =========================================================
    # MAIN GRAPH BUILDER
    # =========================================================

    def build_event_graph(
        self,
        graph_id: str,
        max_depth: int = 3,
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # Validate depth
        # -----------------------------------------------------

        try:
            max_depth = int(max_depth)
        except (TypeError, ValueError):
            max_depth = 3

        max_depth = max(
            1,
            min(max_depth, 5),
        )

        # -----------------------------------------------------
        # Neo4j connection
        # -----------------------------------------------------

        if not self.neo4j.verify_connection():
            return {
                "success": False,
                "message": "Neo4j connection failed.",
            }

        # =====================================================
        # 1. FIND EVENT
        # =====================================================

        event_query = """
        MATCH (e:Event {graph_id: $graph_id})
        RETURN e
        LIMIT 1
        """

        event_records = self.neo4j.execute_query(
            event_query,
            {
                "graph_id": graph_id,
            },
        )

        if not event_records:
            return {
                "success": False,
                "message": f"Event graph not found: {graph_id}",
            }

        event_node = event_records[0]["e"]

        # =====================================================
        # 2. FIND CONNECTED NODES
        #
        # max_depth is validated and embedded as an integer.
        # It is NOT passed as a Cypher parameter.
        # =====================================================

        nodes_query = f"""
        MATCH (e:Event {{graph_id: $graph_id}})

        OPTIONAL MATCH (e)-[*1..{max_depth}]-(n)

        WITH e, collect(DISTINCT n) AS related_nodes

        UNWIND ([e] + related_nodes) AS node

        WITH DISTINCT node

        WHERE node IS NOT NULL

        RETURN
            node.graph_id AS graph_id,
            labels(node) AS labels,
            properties(node) AS properties
        """

        node_records = self.neo4j.execute_query(
            nodes_query,
            {
                "graph_id": graph_id,
            },
        )

        # =====================================================
        # 3. BUILD RAW NODE DATA
        # =====================================================

        raw_nodes: list[dict[str, Any]] = []

        for record in node_records:

            node_graph_id = record.get(
                "graph_id"
            )

            if not node_graph_id:
                continue

            raw_nodes.append(
                {
                    "graph_id": str(node_graph_id),
                    "labels": list(
                        record.get(
                            "labels",
                            [],
                        )
                    ),
                    "properties": dict(
                        record.get(
                            "properties",
                            {},
                        )
                    ),
                }
            )

        # =====================================================
        # 4. REMOVE DUPLICATE NODES
        # =====================================================

        unique_nodes: dict[str, dict[str, Any]] = {}

        for node in raw_nodes:

            node_graph_id = node["graph_id"]

            unique_nodes[
                node_graph_id
            ] = node

        # =====================================================
        # 5. EVENT MUST BE FIRST
        # =====================================================

        ordered_nodes: list[dict[str, Any]] = []

        if graph_id in unique_nodes:

            ordered_nodes.append(
                unique_nodes.pop(graph_id)
            )

        else:

            # Extremely defensive fallback.
            event_properties = dict(
                event_node
            )

            ordered_nodes.append(
                {
                    "graph_id": graph_id,
                    "labels": ["Event"],
                    "properties": event_properties,
                }
            )

        # -----------------------------------------------------
        # Add all remaining nodes.
        #
        # Other Event nodes are excluded.
        # -----------------------------------------------------

        for node in unique_nodes.values():

            if "Event" in node["labels"]:
                continue

            ordered_nodes.append(node)

        # =====================================================
        # 6. GRAPH_ID → INDEX
        # =====================================================

        node_index: dict[str, int] = {}

        for index, node in enumerate(
            ordered_nodes
        ):

            node_index[
                node["graph_id"]
            ] = index

        selected_graph_ids = list(
            node_index.keys()
        )

        # =====================================================
        # 7. GET RELATIONSHIPS
        #
        # IMPORTANT:
        # We identify nodes using graph_id.
        # No elementId().
        # =====================================================

        relationships_query = """
        MATCH (source)-[r]->(target)

        WHERE source.graph_id IN $graph_ids
          AND target.graph_id IN $graph_ids

        RETURN
            source.graph_id AS source_graph_id,
            target.graph_id AS target_graph_id,
            type(r) AS relationship_type,
            properties(r) AS relationship_properties
        """

        relationship_records = (
            self.neo4j.execute_query(
                relationships_query,
                {
                    "graph_ids": selected_graph_ids,
                },
            )
        )

        relationships: list[
            dict[str, Any]
        ] = []

        seen_relationships = set()

        for record in relationship_records:

            source_graph_id = record.get(
                "source_graph_id"
            )

            target_graph_id = record.get(
                "target_graph_id"
            )

            relationship_type = record.get(
                "relationship_type",
                "RELATED_TO",
            )

            if (
                not source_graph_id
                or not target_graph_id
            ):
                continue

            if (
                source_graph_id
                not in node_index
                or target_graph_id
                not in node_index
            ):
                continue

            if (
                relationship_type
                not in self.RELATIONSHIP_TYPES
            ):
                relationship_type = "RELATED_TO"

            source_index = node_index[
                source_graph_id
            ]

            target_index = node_index[
                target_graph_id
            ]

            relationship_key = (
                source_index,
                target_index,
                relationship_type,
            )

            if (
                relationship_key
                in seen_relationships
            ):
                continue

            seen_relationships.add(
                relationship_key
            )

            relationship_properties = dict(
                record.get(
                    "relationship_properties",
                    {},
                )
                or {}
            )

            relationships.append(
                {
                    "source": source_index,
                    "target": target_index,
                    "relationship": relationship_type,
                    "properties": relationship_properties,
                }
            )

        # =====================================================
        # 8. CALCULATE NODE DEGREE
        # =====================================================

        degrees: dict[int, int] = {}

        for relationship in relationships:

            source = relationship["source"]
            target = relationship["target"]

            degrees[source] = (
                degrees.get(source, 0) + 1
            )

            degrees[target] = (
                degrees.get(target, 0) + 1
            )

        # =====================================================
        # 9. NODE FEATURES
        #
        # 10 features:
        #
        # 0 Event
        # 1 Supplier
        # 2 Product
        # 3 Facility
        # 4 Location
        # 5 Entity
        # 6 Severity
        # 7 Risk
        # 8 Degree
        # 9 Bias
        # =====================================================

        x: list[list[float]] = []

        node_types: list[str] = []
        node_names: list[str] = []

        for index, node in enumerate(
            ordered_nodes
        ):

            node_labels = node["labels"]
            node_properties = node[
                "properties"
            ]

            node_type = self._get_node_type(
                node_labels,
                node_properties,
            )

            node_name = self._get_node_name(
                node_properties
            )

            node_types.append(
                node_type
            )

            node_names.append(
                node_name
            )

            feature = [0.0] * 10

            type_index = self.NODE_TYPES.get(
                node_type,
                self.NODE_TYPES["Entity"],
            )

            feature[type_index] = 1.0

            # -------------------------------------------------
            # Severity
            # -------------------------------------------------

            severity = str(
                node_properties.get(
                    "severity",
                    "",
                )
            ).lower()

            feature[6] = {
                "low": 0.25,
                "medium": 0.50,
                "high": 0.75,
                "critical": 1.00,
            }.get(
                severity,
                0.50,
            )

            # -------------------------------------------------
            # Risk / impact
            # -------------------------------------------------

            risk_value = node_properties.get(
                "risk_score",
                node_properties.get(
                    "impact_score",
                    0.0,
                ),
            )

            try:
                risk_value = float(
                    risk_value
                )
            except (
                TypeError,
                ValueError,
            ):
                risk_value = 0.0

            if risk_value > 1:
                risk_value /= 100.0

            feature[7] = max(
                0.0,
                min(1.0, risk_value),
            )

            # -------------------------------------------------
            # Degree
            # -------------------------------------------------

            feature[8] = min(
                1.0,
                degrees.get(
                    index,
                    0,
                )
                / 10.0,
            )

            # -------------------------------------------------
            # Bias
            # -------------------------------------------------

            feature[9] = 1.0

            x.append(feature)

        # =====================================================
        # 10. EDGE INDEX
        # =====================================================

        edge_index = [
            [],
            [],
        ]

        for relationship in relationships:

            edge_index[0].append(
                relationship["source"]
            )

            edge_index[1].append(
                relationship["target"]
            )

        # =====================================================
        # 11. SERIALIZED NODES
        # =====================================================

        serialized_nodes = []

        for index, node in enumerate(
            ordered_nodes
        ):

            node_properties = node[
                "properties"
            ]

            serialized_nodes.append(
                {
                    "index": index,
                    "graph_id": node[
                        "graph_id"
                    ],
                    "name": self._get_node_name(
                        node_properties
                    ),
                    "node_type": node_types[
                        index
                    ],
                    "properties": node_properties,
                }
            )

        # =====================================================
        # 12. FINAL RESULT
        # =====================================================

        return {
            "success": True,
            "graph_id": graph_id,
            "num_nodes": len(
                serialized_nodes
            ),
            "num_edges": len(
                relationships
            ),
            "num_node_features": 10,
            "node_types": node_types,
            "node_names": node_names,
            "nodes": serialized_nodes,
            "relationships": relationships,
            "x": x,
            "edge_index": edge_index,
        }

    # =========================================================
    # NODE TYPE
    # =========================================================

    def _get_node_type(
        self,
        labels: list[str],
        properties: dict[str, Any],
    ) -> str:

        priority = [
            "Event",
            "Supplier",
            "Product",
            "Facility",
            "Location",
            "Person",
            "Group",
            "Organization",
            "Entity",
        ]

        for label in priority:

            if label in labels:
                return label

        # Property-based fallback.

        if properties.get(
            "event_id"
        ) is not None:
            return "Event"

        if properties.get(
            "supplier_id"
        ) is not None:
            return "Supplier"

        if properties.get(
            "product_id"
        ) is not None:
            return "Product"

        return "Entity"

    # =========================================================
    # NODE NAME
    # =========================================================

    def _get_node_name(
        self,
        properties: dict[str, Any],
    ) -> str:

        for key in (
            "title",
            "name",
            "label",
        ):

            value = properties.get(key)

            if value:
                return str(value)

        return "Unknown"