from typing import Any

from ml.graph.neo4j_client import neo4j_client


CREATE_EVENT_QUERY = """
MERGE (e:Event {id: $event_id})
SET
    e.title = $title,
    e.event_type = $event_type,
    e.description = $description,
    e.source = $source,
    e.location = $location
RETURN e
"""


def create_event_node(event: dict[str, Any]) -> dict[str, Any]:
    """
    Create or update an Event node in Neo4j.
    """

    event_id = event.get("id")

    if event_id is None:
        raise ValueError("Event must contain an 'id'.")

    parameters = {
        "event_id": event_id,
        "title": event.get("title", ""),
        "event_type": event.get("event_type", "unknown"),
        "description": event.get("description", ""),
        "source": event.get("source", ""),
        "location": event.get("location", ""),
    }

    with neo4j_client._driver.session() as session:
        result = session.run(
            CREATE_EVENT_QUERY,
            parameters,
        )

        record = result.single()

    return dict(record["e"])