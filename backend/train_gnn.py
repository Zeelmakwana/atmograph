from __future__ import annotations

import os

import torch
import torch.nn.functional as F

from app.services.gnn_model import AtmoGraphGNN
from app.services.gnn_training_service import (
    GNNTrainingService,
)
from app.services.neo4j_service import Neo4jService


MODEL_DIR = "models"
MODEL_PATH = os.path.join(
    MODEL_DIR,
    "atmograph_gnn.pt",
)

EPOCHS = 100
LEARNING_RATE = 0.01


def main() -> None:

    print("=" * 60)
    print("AtmoGraph GNN Training")
    print("=" * 60)

    neo4j = Neo4jService()

    try:

        if not neo4j.verify_connection():
            print(
                "ERROR: Neo4j connection failed."
            )
            return

        print(
            "✓ Neo4j connection successful"
        )

        service = GNNTrainingService(
            neo4j
        )

        graphs = (
            service.build_training_graphs()
        )

        if not graphs:
            print(
                "ERROR: No training graphs found."
            )
            return

        print(
            f"✓ Training graphs: {len(graphs)}"
        )

        total_nodes = sum(
            graph.num_nodes
            for graph in graphs
        )

        total_edges = sum(
            graph.num_edges
            for graph in graphs
        )

        print(
            f"✓ Training nodes: {total_nodes}"
        )

        print(
            f"✓ Training edges: {total_edges}"
        )

        # ---------------------------------------------------------
        # Model
        # ---------------------------------------------------------

        model = AtmoGraphGNN(
            input_features=10,
            hidden_features=32,
            output_features=1,
        )

        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=LEARNING_RATE,
            weight_decay=0.0005,
        )

        model.train()

        # ---------------------------------------------------------
        # Training
        # ---------------------------------------------------------

        for epoch in range(
            1,
            EPOCHS + 1,
        ):

            optimizer.zero_grad()

            total_loss = 0.0

            for graph in graphs:

                prediction = model(
                    graph.x,
                    graph.edge_index,
                )

                loss = F.mse_loss(
                    prediction,
                    graph.y,
                )

                loss.backward()

                total_loss += loss.item()

            optimizer.step()

            if (
                epoch == 1
                or epoch % 10 == 0
            ):

                average_loss = (
                    total_loss
                    / len(graphs)
                )

                print(
                    f"Epoch "
                    f"{epoch:03d}/{EPOCHS} "
                    f"| Loss: "
                    f"{average_loss:.6f}"
                )

        # ---------------------------------------------------------
        # Save
        # ---------------------------------------------------------

        os.makedirs(
            MODEL_DIR,
            exist_ok=True,
        )

        torch.save(
            {
                "model_state_dict":
                    model.state_dict(),
                "input_features": 10,
                "hidden_features": 32,
                "output_features": 1,
            },
            MODEL_PATH,
        )

        print()
        print(
            f"✓ Model saved: {MODEL_PATH}"
        )

        print("=" * 60)
        print("Training completed successfully.")
        print("=" * 60)

    finally:

        neo4j.close()


if __name__ == "__main__":
    main()