from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.gnn_prediction_service import GNNPredictionService
from app.services.neo4j_service import Neo4jService
from app.services.prediction_engine import predict_event_impact


class HybridPredictionService:
    """
    Combines:
        40% rule-based prediction
        60% GNN prediction
    """

    def __init__(self):
        self.neo4j = Neo4jService()
        self.gnn_service = GNNPredictionService(
            neo4j=self.neo4j
        )

    def predict(
        self,
        db: Session,
        event_id: int,
        graph_id: str,
    ) -> dict[str, Any]:

        # ---------------------------------------------
        # Existing rule-based prediction
        # ---------------------------------------------

        base_result = predict_event_impact(
            db=db,
            event_id=event_id,
        )

        if base_result is None:
            return {
                "success": False,
                "error": f"Event {event_id} not found.",
            }

        base_score = float(
            base_result.get(
                "risk_score",
                0.0,
            )
        )

        # ---------------------------------------------
        # GNN prediction
        # ---------------------------------------------

        gnn_result = self.gnn_service.predict(
            graph_id
        )

        if not gnn_result.get("success"):
            return {
                "success": False,
                "error": gnn_result.get(
                    "error",
                    "GNN prediction failed.",
                ),
            }

        gnn_score = float(
            gnn_result.get(
                "overall_risk_score",
                0.0,
            )
        )

        # ---------------------------------------------
        # Hybrid score
        # ---------------------------------------------

        final_score = (
            base_score * 0.40
            + gnn_score * 0.60
        )

        final_score = round(
            max(
                0.0,
                min(
                    100.0,
                    final_score,
                ),
            ),
            2,
        )

        return {
            "success": True,
            "event_id": event_id,
            "graph_id": graph_id,

            "base_prediction": {
                "risk_score": base_score,
                "risk_level": base_result.get(
                    "risk_level"
                ),
                "affected_suppliers": base_result.get(
                    "affected_suppliers",
                    [],
                ),
                "affected_products": base_result.get(
                    "affected_products",
                    [],
                ),
                "estimated_delay_days": (
                    self._get_delay(
                        base_result
                    )
                ),
            },

            "gnn_prediction": {
                "risk_score": round(
                    gnn_score,
                    2,
                ),
                "model": gnn_result.get(
                    "model",
                    "AtmoGraphGNN",
                ),
                "model_loaded": gnn_result.get(
                    "model_loaded",
                    False,
                ),
                "node_predictions": (
                    gnn_result.get(
                        "node_predictions",
                        [],
                    )
                ),
            },

            "hybrid_prediction": {
                "risk_score": final_score,
                "risk_level": self._risk_level(
                    final_score
                ),
            },

            "weights": {
                "rule_based": 0.40,
                "gnn": 0.60,
            },
        }

    @staticmethod
    def _get_delay(
        result: dict[str, Any],
    ) -> int:

        impacts = result.get(
            "impacts",
            [],
        )

        delays = [
            item.get(
                "estimated_delay_days",
                0,
            )
            for item in impacts
            if item.get(
                "estimated_delay_days"
            ) is not None
        ]

        if not delays:
            return 0

        return round(
            sum(delays) / len(delays)
        )

    @staticmethod
    def _risk_level(
        score: float,
    ) -> str:

        if score >= 75:
            return "critical"

        if score >= 50:
            return "high"

        if score >= 30:
            return "medium"

        return "low"