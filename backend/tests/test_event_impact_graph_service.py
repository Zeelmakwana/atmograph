from __future__ import annotations

import pytest

from app.services.event_impact_graph_service import (
    EventImpactGraphService,
)


def test_service_imports():
    assert EventImpactGraphService is not None


def test_normalize_name():
    assert (
        EventImpactGraphService._normalize_name(
            "Global-Components_Ltd"
        )
        == "global components ltd"
    )


def test_number_conversion():
    assert (
        EventImpactGraphService._number(
            "10"
        )
        == 10.0
    )

    assert (
        EventImpactGraphService._number(
            None
        )
        == 0.0
    )

    assert (
        EventImpactGraphService._number(
            "invalid"
        )
        == 0.0
    )


def test_number_default():
    assert (
        EventImpactGraphService._number(
            None,
            5.0,
        )
        == 5.0
    )