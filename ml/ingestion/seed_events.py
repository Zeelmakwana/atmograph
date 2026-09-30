from app.core.database import SessionLocal
from app.core.init_db import initialize_database

from ml.ingestion.event_loader import save_news_items


SAMPLE_EVENTS = [
    {
        "title": "Rotterdam Port Strike",
        "description": "Workers at Rotterdam port announce a strike that may delay cargo shipments.",
        "source": "Demo News",
        "event_type": "port_strike",
        "location": "Rotterdam, Netherlands",
    },
    {
        "title": "Severe Storm Disrupts Shipping",
        "description": "Severe weather conditions may interrupt maritime transportation.",
        "source": "Demo News",
        "event_type": "weather_disruption",
        "location": "North Sea",
    },
]


def seed_events() -> None:
    initialize_database()

    db = SessionLocal()

    try:
        events = save_news_items(SAMPLE_EVENTS, db)

        print(f"Inserted {len(events)} events.")

        for event in events:
            print(f"[{event.id}] {event.title}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_events()