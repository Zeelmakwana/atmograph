from ml.ingestion.news_parser import parse_news
from ml.nlp.entity_extractor import extract_event_entities


def build_event(
    title: str,
    content: str,
    source: str | None = None,
) -> dict:
    """
    Build a structured AtmoGraph event from raw news data.
    """

    news = parse_news(
        title=title,
        content=content,
        source=source,
    )

    entities = extract_event_entities(news["content"])

    return {
        "title": news["title"],
        "content": news["content"],
        "source": news["source"],
        "ingested_at": news["ingested_at"],
        "entities": entities,
    }