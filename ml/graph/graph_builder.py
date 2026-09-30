"""
AtmoGraph Graph Builder

Purpose:
    Converts supply-chain event information into graph nodes
    and relationships for Neo4j.

Graph concept:

    Event
      |
      | AFFECTS
      ↓
    Location

    Event
      |
      | AFFECTS
      ↓
    Organization
"""


from typing import Any

from ml.graph.neo4j_client import neo4j_client


def create_event_graph(event_data: dict[str, Any]) -> dict[str, Any]:
    """
    Create graph representation for one supply-chain event.

    Args:
        event_data:
            Event information including title, location,
            organizations and event metadata.

    Returns:
        Dictionary containing created graph information.
    """

    event_id = event_data.get("id")
    title = event_data.get("title", "Unknown Event")
    location = event_data.get("location")
    organizations = event_data.get("organizations", [])

    if not event_id:
        raise ValueError("Event ID is required.")

    if not location:
        raise ValueError("Event location is required.")

    event_query = """
    MERGE (e:Event {id: $event_id})
    SET e.title = $title
    RETURN e
    """

    location_query = """
    MERGE (l:Location {name: $location})
    RETURN l
    """

    relationship_query = """
    MATCH (e:Event {id: $event_id})
    MATCH (l:Location {name: $location})
    MERGE (e)-[:AFFECTS]->(l)
    """

    neo4j_client.execute_query(
        event_query,
        {
            "event_id": event_id,
            "title": title,
        },
    )

    neo4j_client.execute_query(
        location_query,
        {
            "location": location,
        },
    )

    neo4j_client.execute_query(
        relationship_query,
        {
            "event_id": event_id,
            "location": location,
        },
    )

    for organization in organizations:
        organization_query = """
        MERGE (o:Organization {name: $organization})
        RETURN o
        """

        organization_relationship_query = """
        MATCH (e:Event {id: $event_id})
        MATCH (o:Organization {name: $organization})
        MERGE (e)-[:AFFECTS]->(o)
        """

        neo4j_client.execute_query(
            organization_query,
            {
                "organization": organization,
            },
        )

        neo4j_client.execute_query(
            organization_relationship_query,
            {
                "event_id": event_id,
                "organization": organization,
            },
        )

    return {
        "event_id": event_id,
        "location": location,
        "organizations": organizations,
        "status": "graph_created",
    }