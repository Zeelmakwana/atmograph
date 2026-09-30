"""
News Ingestion Pipeline

Purpose:
    Connects the news parser with the database event ingestor.

Flow:
    Raw News
        ↓
    News Parser
        ↓
    Structured Event
        ↓
    Event Ingestor
        ↓
    SQLite Database
"""

from ml.ingestion.news_parser import parse_news
from ml.ingestion.event_ingestor import ingest_event


def run_ingestion(
    title: str,
    content: str,
    source: str,
):
    """
    Parse raw news and store it as an Event.
    """

    parsed_event = parse_news(
        title=title,
        content=content,
        source=source,
        event_type="supply_chain_disruption",
        location="Rotterdam, Netherlands",
        severity="high",
    )

    event = ingest_event(parsed_event)

    return event


if __name__ == "__main__":
    event = run_ingestion(
        title="Rotterdam Port Strike",
        content=(
            "A strike at Rotterdam port is causing "
            "shipping delays across Europe."
        ),
        source="Reuters",
    )

    print("INGESTION SUCCESS")
    print(f"Event ID: {event.id}")
    print(f"Title: {event.title}")
    print(f"Event Type: {event.event_type}")
    print(f"Location: {event.location}")
    print(f"Severity: {event.severity}")
    print(f"Status: {event.status}")