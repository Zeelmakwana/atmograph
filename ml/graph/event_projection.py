"""Build a Neo4j-ready graph projection without requiring Neo4j to run.

The projection is deliberately a plain dictionary so it can be inspected,
tested, queued, or later written by :mod:`ml.graph.graph_builder`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


_LOCATION_ENTITY_LABELS = {"GPE", "LOC", "FAC"}


def _normalise_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    cleaned = " ".join(value.split())
    return cleaned or None


def _entity_names(
    entities: Iterable[Mapping[str, object]] | None,
    labels: set[str],
) -> list[str]:
    """Return unique entity names for the requested spaCy entity labels."""
    if not entities:
        return []

    names: list[str] = []
    seen: set[str] = set()
    for entity in entities:
        if str(entity.get("label", "")).upper() not in labels:
            continue

        name = _normalise_name(entity.get("text"))
        if name and name.casefold() not in seen:
            names.append(name)
            seen.add(name.casefold())

    return names


def build_event_projection(
    event: Mapping[str, Any],
    entities: Iterable[Mapping[str, object]] | None = None,
) -> dict[str, Any]:
    """Create nodes and relationships for a single stored supply-chain event.

    ``event`` must include its SQLite ``id``.  Locations are gathered from the
    explicit event location and location-like NLP entities; organisations come
    from ``ORG`` entities.  Every graph identifier is stable for repeatable
    Neo4j ``MERGE`` operations.
    """
    event_id = event.get("id")
    if event_id is None:
        raise ValueError("Event must contain an 'id' before it can be projected.")

    event_key = f"event:{event_id}"
    event_properties = {
        "id": event_id,
        "title": _normalise_name(event.get("title")) or "Untitled Event",
        "event_type": _normalise_name(event.get("event_type")) or "unknown",
        "description": _normalise_name(event.get("description")) or "",
        "source": _normalise_name(event.get("source")) or "",
        "severity": event.get("severity", "medium"),
        "status": _normalise_name(event.get("status")) or "active",
    }
    nodes = [{"id": event_key, "labels": ["Event"], "properties": event_properties}]
    relationships: list[dict[str, str]] = []

    locations: list[str] = []
    explicit_location = _normalise_name(event.get("location"))
    if explicit_location:
        locations.append(explicit_location)
    for location in _entity_names(entities, _LOCATION_ENTITY_LABELS):
        if location.casefold() not in {item.casefold() for item in locations}:
            locations.append(location)

    for location in locations:
        target = f"location:{location.casefold()}"
        nodes.append({"id": target, "labels": ["Location"], "properties": {"name": location}})
        relationships.append({"source": event_key, "target": target, "type": "AFFECTS"})

    for organisation in _entity_names(entities, {"ORG"}):
        target = f"organization:{organisation.casefold()}"
        nodes.append({"id": target, "labels": ["Organization"], "properties": {"name": organisation}})
        relationships.append({"source": event_key, "target": target, "type": "AFFECTS"})

    return {
        "event_id": event_id,
        "nodes": nodes,
        "relationships": relationships,
        "summary": {
            "location_count": len(locations),
            "organization_count": sum("Organization" in node["labels"] for node in nodes),
        },
    }
