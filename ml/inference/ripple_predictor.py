"""Deterministic baseline ripple prediction for an event graph projection.

This is a transparent baseline, not a trained model.  It gives the API and
future GNN training pipeline a stable prediction contract before graph data is
available in Neo4j.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_SEVERITY_SCORES = {"low": 0.30, "medium": 0.55, "high": 0.75, "critical": 0.95}
_DISRUPTION_TYPES = {"supply_chain_disruption", "port_closure", "strike", "natural_disaster"}


def _severity_score(value: object) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(float(value) / 5.0, 1.0))
    return _SEVERITY_SCORES.get(str(value).strip().lower(), _SEVERITY_SCORES["medium"])


def predict_ripple(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Rank graph targets by their estimated disruption exposure.

    The result contains only direct event targets today.  Once Neo4j is online,
    a GNN can preserve this contract while adding multi-hop targets.
    """
    nodes = {str(node["id"]): node for node in projection.get("nodes", [])}
    event_id = projection.get("event_id")
    event_node = nodes.get(f"event:{event_id}")
    if event_node is None:
        raise ValueError("Projection does not contain its Event node.")

    properties = event_node.get("properties", {})
    base_score = _severity_score(properties.get("severity"))
    if str(properties.get("event_type", "")).strip().lower() in _DISRUPTION_TYPES:
        base_score = min(base_score + 0.10, 1.0)

    predictions: list[dict[str, Any]] = []
    for relationship in projection.get("relationships", []):
        if relationship.get("source") != f"event:{event_id}" or relationship.get("type") != "AFFECTS":
            continue
        target = nodes.get(str(relationship.get("target")))
        if not target:
            continue

        target_type = target.get("labels", ["Unknown"])[0]
        score = min(base_score + (0.05 if target_type == "Organization" else 0.0), 1.0)
        predictions.append({
            "target_id": target["id"],
            "target_name": target.get("properties", {}).get("name", target["id"]),
            "target_type": target_type,
            "risk_score": round(score, 2),
            "risk_level": "high" if score >= 0.70 else "medium" if score >= 0.40 else "low",
            "explanation": "Directly affected by the event graph relationship.",
        })

    predictions.sort(key=lambda item: (-item["risk_score"], item["target_name"]))
    return {
        "event_id": event_id,
        "model": "deterministic-baseline-v1",
        "predictions": predictions,
    }
