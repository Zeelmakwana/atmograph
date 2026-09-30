from app.core.database import SessionLocal
from app.models import Event

from ml.graph.event_graph import create_event_node


def sync_events_to_neo4j() -> int:
    """
    Sync all events from SQLite to Neo4j.
    """

    db = SessionLocal()
    synced_count = 0

    try:
        events = db.query(Event).all()

        for event in events:
            event_data = {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "source": event.source,
                "event_type": event.event_type,
                "location": event.location,
            }

            create_event_node(event_data)
            synced_count += 1

        return synced_count

    finally:
        db.close()


if __name__ == "__main__":
    count = sync_events_to_neo4j()
    print(f"Synced {count} events to Neo4j.")