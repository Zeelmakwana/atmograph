from __future__ import annotations

from typing import Any

import torch

from app.services.gnn_model import AtmoGraphGNN
from app.services.gnn_graph_service import GNNGraphService
from app.services.neo4j_service import Neo4jService


class GNNPredictionService:
    """
    Runs AtmoGraph GNN inference on a Neo4j-derived graph.
    """

    def __init__(
        self,
        neo4j: Neo4jService,
    ) -> None:

        self.neo4j = neo4j

        self.model = AtmoGraphGNN(
            input_features=10,
            hidden_features=32,
            output_features=1,
        )

        model_path = "models/atmograph_gnn.pt"

        try:

            checkpoint = torch.load(
                model_path,
                map_location="cpu",
                weights_only=True,
            )

            self.model.load_state_dict(
                checkpoint["model_state_dict"]
            )

            self.model_loaded = True

        except (
            FileNotFoundError,
            RuntimeError,
            KeyError,
        ):

            self.model_loaded = False

        self.model.eval()

    def predict(
        self,
        graph_id: str,
    ) -> dict[str, Any]:

        graph_service = GNNGraphService(
            self.neo4j
        )

        graph_result = (
            graph_service.build_event_graph(
                graph_id=graph_id,
                max_depth=3,
            )
        )

        if not graph_result.get("success"):
            return graph_result

        x = torch.tensor(
            graph_result["x"],
            dtype=torch.float,
        )

        edge_index = torch.tensor(
            graph_result["edge_index"],
            dtype=torch.long,
        )

        # PyG expects shape [2, number_of_edges]
        if edge_index.numel() == 0:
            edge_index = torch.empty(
                (2, 0),
                dtype=torch.long,
            )

        with torch.no_grad():

            predictions = self.model(
                x,
                edge_index,
            )

        predictions = (
            predictions
            .squeeze(-1)
            .tolist()
        )

        # Convert raw output into 0-100 range

        risk_scores = []

        for value in predictions:

            score = float(value) * 100.0

            score = max(
                0.0,
                min(100.0, score),
            )

            risk_scores.append(
                round(score, 2)
            )

        node_predictions = []

        for index, name in enumerate(
            graph_result["node_names"]
        ):

            node_type = (
                graph_result["node_types"][
                    index
                ]
            )

            node_predictions.append(
                {
                    "node": name,
                    "node_type": node_type,
                    "risk_score": risk_scores[
                        index
                    ],
                }
            )

        overall_risk = (
            max(risk_scores)
            if risk_scores
            else 0.0
        )

        return {
            "success": True,
            "graph_id": graph_id,
            "model": "AtmoGraphGNN",
            "architecture": "GCN",
            "num_nodes": graph_result[
                "num_nodes"
            ],
            "num_edges": graph_result[
                "num_edges"
            ],
            "overall_risk_score": round(
                overall_risk,
                2,
            ),
            "node_predictions": node_predictions,
            "model_loaded": self.model_loaded,
        }