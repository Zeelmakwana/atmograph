import spacy


def load_nlp_model():
    """
    Load the spaCy English NLP model.
    """
    return spacy.load("en_core_web_sm")


def extract_entities(text: str) -> list[dict[str, str]]:
    """
    Extract named entities from text.
    """

    nlp = load_nlp_model()
    doc = nlp(text)

    entities = []

    for entity in doc.ents:
        entities.append(
            {
                "text": entity.text,
                "label": entity.label_,
            }
        )

    return entities


def extract_event_entities(
    title: str,
    description: str = "",
) -> list[dict[str, str]]:
    """
    Extract entities from an event title and description.
    """

    text = f"{title}. {description}".strip()

    return extract_entities(text)