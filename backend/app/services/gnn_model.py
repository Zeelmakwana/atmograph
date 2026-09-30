from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import GCNConv


class AtmoGraphGNN(nn.Module):
    """
    Graph Convolutional Network for AtmoGraph.

    Input:
        x          -> node features
        edge_index -> graph connections

    Output:
        risk score for each node
    """

    def __init__(
        self,
        input_features: int = 10,
        hidden_features: int = 32,
        output_features: int = 1,
    ) -> None:

        super().__init__()

        self.conv1 = GCNConv(
            input_features,
            hidden_features,
        )

        self.conv2 = GCNConv(
            hidden_features,
            hidden_features,
        )

        self.output_layer = nn.Linear(
            hidden_features,
            output_features,
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:

        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.output_layer(x)
        return torch.sigmoid(x)