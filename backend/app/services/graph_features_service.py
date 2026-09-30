from __future__ import annotations

from typing import Any

from app.services.neo4j_service import Neo4jService


class GraphFeaturesService:
    """
    Extract numerical graph features from an AtmoGraph event.

    These features will later become inputs for the GNN.
    """

    def __init__(self, neo4j: Neo4jService) -> None:
        self.neo4j = neo4j

    def extract_event_features(
        self,
        graph_id: str,
    ) -> dict[str, Any]:
        """
        Extract graph-level intelligence for an NLP event.
        """

        if not self.neo4j.verify_connection():
            return {
                "success": False,
                "message": "Unable to connect to Neo4j.",
            }

        # =========================================================
        # EVENT
        # =========================================================

        event_query = """
        MATCH (e:Event {graph_id: $graph_id})

        RETURN
            e.graph_id AS graph_id,
            e.name AS name,
            e.event_type AS event_type,
            e.severity AS severity
        """

        event_result = self.neo4j.execute_query(
            event_query,
            {"graph_id": graph_id},
        )

        if not event_result:
            return {
                "success": False,
                "message": "Event not found in Neo4j.",
            }

        event = event_result[0]

        # =========================================================
        # SUPPLIERS + PRODUCTS
        # =========================================================

        supply_chain_query = """
        MATCH (e:Event {graph_id: $graph_id})

        OPTIONAL MATCH (e)-[:INVOLVES]->(s:Supplier)

        OPTIONAL MATCH (s)-[:SUPPLIES]->(p:Product)

        OPTIONAL MATCH (e)-[:OCCURS_AT]->(f:Facility)

        RETURN
            count(DISTINCT s) AS supplier_count,
            count(DISTINCT p) AS product_count,
            count(DISTINCT f) AS facility_count
        """

        supply_result = self.neo4j.execute_query(
            supply_chain_query,
            {"graph_id": graph_id},
        )

        supply_features = (
            supply_result[0]
            if supply_result
            else {
                "supplier_count": 0,
                "product_count": 0,
                "facility_count": 0,
            }
        )

        # =========================================================
        # RIPPLE PATHS
        # =========================================================

        ripple_query = """
        MATCH path =
            (e:Event {graph_id: $graph_id})
            -[*1..5]->
            (downstream)

        RETURN
            count(path) AS path_count,
            max(length(path)) AS max_ripple_depth
        """

        ripple_result = self.neo4j.execute_query(
            ripple_query,
            {"graph_id": graph_id},
        )

        ripple_features = (
            ripple_result[0]
            if ripple_result
            else {
                "path_count": 0,
                "max_ripple_depth": 0,
            }
        )

        path_count = (
            ripple_features.get("path_count")
            or 0
        )

        max_ripple_depth = (
            ripple_features.get(
                "max_ripple_depth"
            )
            or 0
        )

        supplier_count = (
            supply_features.get(
                "supplier_count"
            )
            or 0
        )

        product_count = (
            supply_features.get(
                "product_count"
            )
            or 0
        )

        facility_count = (
            supply_features.get(
                "facility_count"
            )
            or 0
        )

        # =========================================================
        # GRAPH IMPACT SCORE
        # =========================================================

        graph_impact_score = (
            supplier_count * 10
            + product_count * 5
            + facility_count * 8
            + path_count * 2
            + max_ripple_depth * 5
        )

        graph_impact_score = min(
            graph_impact_score,
            100,
        )

        # =========================================================
        # FINAL FEATURES
        # =========================================================

        return {
            "success": True,

            "event": {
                "graph_id": event.get(
                    "graph_id"
                ),
                "name": event.get(
                    "name"
                ),
                "event_type": event.get(
                    "event_type"
                ),
                "severity": event.get(
                    "severity"
                ),
            },

            "features": {
                "supplier_count": supplier_count,
                "product_count": product_count,
                "facility_count": facility_count,
                "path_count": path_count,
                "max_ripple_depth": max_ripple_depth,
                "graph_impact_score": graph_impact_score,
            },
        }