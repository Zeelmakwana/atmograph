from datetime import datetime
from typing import Any


def normalize_news_item(item: dict[str, Any]) -> dict[str, Any]:
    """
    Convert raw news data into AtmoGraph's standard event format.
    """

    return {
        "title": str(item.get("title", "")).strip(),
        "description": str(item.get("description", "")).strip(),
        "source": str(item.get("source", "unknown")).strip(),
        "event_type": str(item.get("event_type", "unknown")).strip(),
        "location": str(item.get("location", "")).strip(),
        "event_time": item.get("event_time"),
        "ingested_at": datetime.utcnow(),
    }


def validate_news_item(item: dict[str, Any]) -> bool:
    """
    Check whether the minimum information required for an event exists.
    """

    title = item.get("title")
    source = item.get("source")

    return bool(title and source)


def prepare_news_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Validate and normalize multiple raw news items.
    """

    prepared = []

    for item in items:
        if validate_news_item(item):
            prepared.append(normalize_news_item(item))

    return prepared