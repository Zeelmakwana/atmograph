"""
News Parser

Purpose:
    Converts raw news information into a normalized AtmoGraph event payload.
"""

from datetime import datetime, timezone
from typing import Optional


def parse_news(
    title: str,
    content: str,
    source: Optional[str] = None,
    event_type: str = "supply_chain_disruption",
    location: Optional[str] = None,
    severity: str = "medium",
) -> dict:
    """
    Convert raw news information into a clean AtmoGraph event payload.
    """

    clean_title = " ".join(title.strip().split())
    clean_content = " ".join(content.strip().split())
    clean_source = source.strip() if source else None
    clean_event_type = event_type.strip()
    clean_location = location.strip() if location else None
    clean_severity = severity.strip().lower()

    if not clean_title:
        raise ValueError("News title cannot be empty.")

    if not clean_content:
        raise ValueError("News content cannot be empty.")

    if not clean_event_type:
        raise ValueError("Event type cannot be empty.")

    return {
        "title": clean_title,
        "content": clean_content,
        "source": clean_source,
        "event_type": clean_event_type,
        "location": clean_location,
        "event_time": datetime.now(timezone.utc),
        "severity": clean_severity,
        "status": "active",
        "ingested_at": datetime.now(timezone.utc),
    }