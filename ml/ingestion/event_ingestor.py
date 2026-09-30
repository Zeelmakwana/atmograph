"""
Event Ingestion Service

Purpose:
    Converts parsed news data into database Event records.
"""

from typing import Any

from app.core.database import SessionLocal
from app.models import Event


def ingest_event(event_data: dict[str, Any]) -> Event:
    """
    Store one parsed event in the database.
    """

    db = SessionLocal()

    try:
        event = Event(
            title=event_data["title"],
            description=event_data["content"],
            source=event_data.get("source"),
            event_type=event_data["event_type"],
            location=event_data.get("location"),
            event_time=event_data["event_time"],
            severity=event_data.get("severity", "medium"),
            status=event_data.get("status", "active"),
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()