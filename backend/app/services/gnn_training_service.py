from __future__ import annotations

from typing import Any

import torch
from torch_geometric.data import Data

from app.services.neo4j_service import Neo4jService


class GNNTrainingService:
    """
    Builds Event-centered training graphs from Neo4j.

    Graph structure:
        Event -> Supplier -> Product
        Event -> Facility
        Event -> other connected entities

    Node features:
        10-dimensional feature vector

    Labels:
        0.0 - 1.0 normalized impact/risk score
    """

    def __init__(
        self,
        neo4j_service: Neo4jService | None = None,
    ):
        self.neo4j = neo4j_service or Neo4jService()

    # =========================================================
    # PUBLIC
    # =========================================================

    def build_training_graphs(self) -> list[Data]:

        if not self.neo4j.verify_connection():
            return []

        events = self._get_events()

        if not events:
            return []

        graphs: list[Data] = []

        for event in events:

            graph = self._build_event_graph(event)

            if graph is not None:
                graphs.append(graph)

        return graphs

    # =========================================================
    # EVENTS
    # =========================================================

    def _get_events(self) -> list[dict[str, Any]]:

        query = """
        MATCH (e:Event)

        RETURN
            elementId(e) AS neo4j_id,
            e.event_id AS event_id,
            e.graph_id AS graph_id,
            e.title AS title,
            e.name AS name,
            e.severity AS severity

        ORDER BY e.event_id
        """

        rows = self.neo4j.execute_query(query)

        events = []

        for row in rows:

            identifier = (
                row.get("graph_id")
                or row.get("event_id")
            )

            if identifier is None:
                continue

            events.append(
                {
                    "neo4j_id": row.get("neo4j_id"),
                    "event_id": row.get("event_id"),
                    "graph_id": row.get("graph_id"),
                    "identifier": str(identifier),
                    "title": row.get("title")
                    or row.get("name"),
                    "severity": row.get("severity"),
                }
            )

        return events

    # =========================================================
    # BUILD EVENT GRAPH
    # =========================================================

    def _build_event_graph(
        self,
        event: dict[str, Any],
    ) -> Data | None:

        identifier = event["identifier"]

        # -----------------------------------------------------
        # Event can be identified using graph_id OR event_id.
        # -----------------------------------------------------

        if event.get("graph_id"):
            where_clause = "e.graph_id = $identifier"
        else:
            where_clause = "e.event_id = $identifier"

        query = f"""
        MATCH (e:Event)
        WHERE {where_clause}

        OPTIONAL MATCH path = (e)-[*1..3]-(connected)

        WITH
            e,
            collect(DISTINCT connected) AS connected_nodes

        OPTIONAL MATCH
            (e)-[direct_rel]->(direct_target)

        WITH
            e,
            connected_nodes,
            collect(
                {{
                    source_id: elementId(e),
                    target_id: elementId(direct_target),
                    type: type(direct_rel),
                    properties: properties(direct_rel)
                }}
            ) AS direct_relationships

        RETURN
            e {{
                .*,
                neo4j_id: elementId(e)
            }} AS event,

            [
                node IN connected_nodes
                WHERE node IS NOT NULL
                |
                node {{
                    .*,
                    neo4j_id: elementId(node)
                }}
            ] AS nodes,

            direct_relationships
        """

        rows = self.neo4j.execute_query(
            query,
            {"identifier": identifier},
        )

        if not rows:
            return None

        row = rows[0]

        event_node = row.get("event")

        if not event_node:
            return None

        connected_nodes = row.get("nodes") or []

        raw_nodes = [event_node] + connected_nodes

        # -----------------------------------------------------
        # UNIQUE NODES
        # -----------------------------------------------------

        nodes: list[dict[str, Any]] = []

        node_index: dict[str, int] = {}

        for node in raw_nodes:

            if not isinstance(node, dict):
                continue

            node_id = str(
                node.get("neo4j_id")
                or node.get("graph_id")
                or node.get("event_id")
                or node.get("supplier_id")
                or node.get("product_id")
                or node.get("name")
            )

            if node_id in node_index:
                continue

            node_index[node_id] = len(nodes)

            nodes.append(node)

        if not nodes:
            return None

        # -----------------------------------------------------
        # NODE FEATURES
        # -----------------------------------------------------

        features = [
            self._build_node_features(node)
            for node in nodes
        ]

        x = torch.tensor(
            features,
            dtype=torch.float32,
        )

        # -----------------------------------------------------
        # EDGES
        # -----------------------------------------------------

        edge_pairs: list[tuple[int, int]] = []

        relationships: list[dict[str, Any]] = []

        direct_relationships = (
            row.get("direct_relationships")
            or []
        )

        for rel in direct_relationships:

            if not isinstance(rel, dict):
                continue

            source_id = str(
                rel.get("source_id")
                or ""
            )

            target_id = str(
                rel.get("target_id")
                or ""
            )

            if (
                source_id not in node_index
                or target_id not in node_index
            ):
                continue

            source = node_index[source_id]
            target = node_index[target_id]

            edge_pairs.append(
                (source, target)
            )

            properties = (
                rel.get("properties")
                or {}
            )

            relationships.append(
                {
                    "source": source,
                    "target": target,
                    "type": rel.get("type"),
                    "impact_level": properties.get(
                        "impact_level"
                    ),
                    "estimated_delay_days": properties.get(
                        "estimated_delay_days"
                    ),
                    "relationship_type": properties.get(
                        "relationship_type"
                    ),
                }
            )

        # -----------------------------------------------------
        # EDGE INDEX
        # -----------------------------------------------------

        if edge_pairs:

            edge_index = torch.tensor(
                edge_pairs,
                dtype=torch.long,
            ).t().contiguous()

        else:

            edge_index = torch.empty(
                (2, 0),
                dtype=torch.long,
            )

        # -----------------------------------------------------
        # LABELS
        # -----------------------------------------------------

        labels = self._build_labels(
            nodes=nodes,
            event=event_node,
            relationships=relationships,
        )

        y = torch.tensor(
            labels,
            dtype=torch.float32,
        ).view(-1, 1)

        return Data(
            x=x,
            edge_index=edge_index,
            y=y,
        )

    # =========================================================
    # NODE FEATURES
    # =========================================================

    def _build_node_features(
        self,
        node: dict[str, Any],
    ) -> list[float]:

        # Neo4j projection does not automatically expose labels
        # inside node properties, so infer node type from fields.

        node_type = self._infer_node_type(node)

        features = [

            # 1 Event
            1.0 if node_type == "Event" else 0.0,

            # 2 Supplier
            1.0 if node_type == "Supplier" else 0.0,

            # 3 Product
            1.0 if node_type == "Product" else 0.0,

            # 4 Facility
            1.0 if node_type == "Facility" else 0.0,

            # 5 Location
            1.0 if node_type == "Location" else 0.0,

            # 6 Other entity
            1.0
            if node_type not in {
                "Event",
                "Supplier",
                "Product",
                "Facility",
                "Location",
            }
            else 0.0,

            # 7 Severity
            self._severity_value(
                node.get("severity")
            ),

            # 8 Supplier ID exists
            1.0
            if node.get("supplier_id") is not None
            else 0.0,

            # 9 Product ID exists
            1.0
            if node.get("product_id") is not None
            else 0.0,

            # 10 Bias/presence feature
            1.0,
        ]

        return features

    # =========================================================
    # NODE TYPE
    # =========================================================

    @staticmethod
    def _infer_node_type(
        node: dict[str, Any],
    ) -> str:

        if node.get("event_id") is not None:
            return "Event"

        if node.get("graph_id", "").startswith(
            "event_"
        ):
            return "Event"

        if node.get("supplier_id") is not None:
            return "Supplier"

        if node.get("product_id") is not None:
            return "Product"

        nlp_type = str(
            node.get("nlp_entity_type")
            or ""
        ).lower()

        if nlp_type == "facility":
            return "Facility"

        if nlp_type == "location":
            return "Location"

        return "Entity"

    # =========================================================
    # LABELS
    # =========================================================

    def _build_labels(
        self,
        nodes: list[dict[str, Any]],
        event: dict[str, Any],
        relationships: list[dict[str, Any]],
    ) -> list[float]:

        event_score = self._severity_value(
            event.get("severity")
        )

        labels = [
            event_score * 0.25
            for _ in nodes
        ]

        # -----------------------------------------------------
        # Event node gets event severity.
        # -----------------------------------------------------

        event_id = str(
            event.get("neo4j_id")
            or event.get("graph_id")
            or event.get("event_id")
            or ""
        )

        for index, node in enumerate(nodes):

            node_id = str(
                node.get("neo4j_id")
                or node.get("graph_id")
                or node.get("event_id")
                or node.get("supplier_id")
                or node.get("product_id")
                or node.get("name")
                or ""
            )

            if node_id == event_id:

                labels[index] = event_score

        # -----------------------------------------------------
        # Relationship impact becomes target node label.
        # -----------------------------------------------------

        for rel in relationships:

            target = rel.get("target")

            if target is None:
                continue

            impact_score = self._impact_value(
                rel.get("impact_level")
            )

            delay = rel.get(
                "estimated_delay_days"
            )

            try:

                delay_score = min(
                    float(delay or 0) / 30.0,
                    1.0,
                )

            except (
                TypeError,
                ValueError,
            ):

                delay_score = 0.0

            relationship_score = max(
                impact_score,
                delay_score,
            )

            if relationship_score > labels[target]:

                labels[target] = relationship_score

        return [
            max(
                0.0,
                min(
                    1.0,
                    float(value),
                ),
            )
            for value in labels
        ]

    # =========================================================
    # SEVERITY
    # =========================================================

    @staticmethod
    def _severity_value(
        severity: Any,
    ) -> float:

        if severity is None:
            return 0.5

        value = str(
            severity
        ).lower().strip()

        # Supports both text and numeric severity.
        mapping = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.55,
            "moderate": 0.55,
            "low": 0.3,
            "minor": 0.2,
        }

        if value in mapping:
            return mapping[value]

        try:

            numeric = float(value)

            # Existing data uses 1-5 severity.
            if numeric <= 5:
                return min(
                    numeric / 5.0,
                    1.0,
                )

            return min(
                numeric / 100.0,
                1.0,
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.5

    # =========================================================
    # IMPACT
    # =========================================================

    @staticmethod
    def _impact_value(
        impact: Any,
    ) -> float:

        if impact is None:
            return 0.0

        value = str(
            impact
        ).lower().strip()

        mapping = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.55,
            "moderate": 0.55,
            "low": 0.3,
            "minor": 0.2,
        }

        return mapping.get(
            value,
            0.0,
        )