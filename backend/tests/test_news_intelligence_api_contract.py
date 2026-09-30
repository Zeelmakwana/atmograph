from app.api.routes.news_intelligence import (
    NewsIntelligenceRequest,
)


def test_news_intelligence_request_supports_auto_simulate():

    payload = NewsIntelligenceRequest(
        title="Hamburg disruption",
        description=(
            "Hamburg port disruption affects shipments."
        ),
        source="manual",
        auto_simulate=True,
    )

    assert (
        payload.auto_simulate
        is True
    )


def test_news_intelligence_request_defaults_to_simulation():

    payload = NewsIntelligenceRequest(
        title="Hamburg disruption",
        description=(
            "Hamburg port disruption affects shipments."
        ),
    )

    assert (
        payload.auto_simulate
        is True
    )
