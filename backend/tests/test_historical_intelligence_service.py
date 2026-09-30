from app.services.historical_intelligence_service import (
    HistoricalIntelligenceService as H,
)


def test_import():
    assert H is not None


def test_normalize():
    result = H._normalize_text(
        "The Hamburg port disruption affects Global Components Ltd."
    )

    assert "hamburg" in result
    assert "disruption" not in result


def test_similarity():
    result = H._text_similarity(
        "Hamburg port disruption",
        "Hamburg port disruption",
    )

    assert result == 1.0


def test_same_family():
    left = {
        "title": "Hamburg port disruption affects Global Components",
        "description": "Shipment delays in Hamburg affect Global Components.",
        "event_type": "supply_chain_disruption",
        "location": "Hamburg",
    }

    right = {
        "title": "Global Components shipment disruption in Hamburg",
        "description": "Global Components faces shipment delays in Hamburg.",
        "event_type": "supply_chain_disruption",
        "location": "Hamburg",
    }

    assert H._cluster_similarity(left, right) >= 0.72


def test_different_type():
    left = {
        "title": "Hamburg port disruption",
        "description": "Shipment delays",
        "event_type": "supply_chain_disruption",
        "location": "Hamburg",
    }

    right = {
        "title": "Hamburg weather disruption",
        "description": "Storm",
        "event_type": "weather_disruption",
        "location": "Hamburg",
    }

    assert H._cluster_similarity(left, right) == 0.0
