from ml.nlp.entity_extractor import extract_event_entities


def analyze_event(
    title: str,
    description: str = "",
    event_type: str = "unknown",
) -> dict:
    """
    Analyze a supply-chain event and return structured NLP information.
    """

    entities = extract_event_entities(
        title=title,
        description=description,
    )

    return {
        "title": title,
        "event_type": event_type,
        "entities": entities,
        "entity_count": len(entities),
    }