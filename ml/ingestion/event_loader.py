from typing import Any

from sqlalchemy.orm import Session

from app.models import Event
from ml.ingestion.news_ingestion import prepare_news_items


def save_news_items(
    items: list[dict[str, Any]],
    db: Session,
) -> list[Event]:
    """
    Validate, normalize, and save news events into the database.
    """

    prepared_items = prepare_news_items(items)
    saved_events = []

    for item in prepared_items:
        event = Event(
            title=item["title"],
            description=item["description"],
            source=item["source"],
            event_type=item["event_type"],
            location=item["location"],
            event_time=item["event_time"],
        )

        db.add(event)
        saved_events.append(event)

    db.commit()

    for event in saved_events:
        db.refresh(event)

    return saved_events