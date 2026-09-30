from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImpactResult:
    impact_score: float
    impact_level: str
    estimated_delay_days: int
    supplier_impact_score: float
    product_impact_score: float
    explanation: str


def _severity_score(severity: Any) -> float:
    """
    Normalize both numeric and textual severity values.

    Supported values:
        1-5
        low
        medium
        high
        critical
    """
    if severity is None:
        return 20.0

    if isinstance(severity, (int, float)):
        value = float(severity)

        # Existing database may use a 1-5 scale.
        if value <= 1:
            return 20.0
        if value <= 2:
            return 40.0
        if value <= 3:
            return 60.0
        if value <= 4:
            return 80.0
        return 100.0

    normalized = str(severity).strip().lower()

    mapping = {
        "low": 25.0,
        "medium": 50.0,
        "moderate": 50.0,
        "high": 75.0,
        "critical": 100.0,
        "severe": 100.0,
    }

    return mapping.get(normalized, 50.0)


def _event_type_score(event_type: str | None) -> float:
    """
    Estimate how strongly an event type can propagate through
    a supply chain.
    """
    if not event_type:
        return 40.0

    normalized = event_type.strip().lower()

    scores = {
        "port_strike": 90.0,
        "supply_chain_disruption": 85.0,
        "port_closure": 95.0,
        "shipping_disruption": 85.0,
        "transport_disruption": 80.0,
        "weather_disruption": 70.0,
        "natural_disaster": 95.0,
        "supplier_failure": 90.0,
        "factory_shutdown": 90.0,
        "labor_strike": 80.0,
        "geopolitical": 85.0,
        "trade_restriction": 80.0,
        "cyber_attack": 85.0,
    }

    for key, score in scores.items():
        if key in normalized:
            return score

    return 50.0


def _status_multiplier(status: str | None) -> float:
    """
    Active events propagate more strongly than resolved events.
    """
    normalized = (status or "active").strip().lower()

    mapping = {
        "active": 1.0,
        "ongoing": 1.0,
        "monitoring": 0.85,
        "pending": 0.75,
        "resolved": 0.25,
        "closed": 0.15,
        "cancelled": 0.10,
    }

    return mapping.get(normalized, 0.75)


def calculate_impact(
    *,
    event_type: str | None,
    severity: Any,
    status: str | None,
    supplier_count: int = 0,
    product_count: int = 0,
) -> ImpactResult:
    """
    Central AtmoGraph impact calculation.

    Flow:

        Event
          ↓
        Severity
          ↓
        Event Type
          ↓
        Status
          ↓
        Suppliers
          ↓
        Products
          ↓
        Impact Score
          ↓
        Delay Estimate
    """

    severity_score = _severity_score(severity)
    event_score = _event_type_score(event_type)
    status_multiplier = _status_multiplier(status)

    supplier_factor = min(supplier_count * 5.0, 20.0)
    product_factor = min(product_count * 3.0, 15.0)

    base_score = (
        severity_score * 0.45
        + event_score * 0.35
        + supplier_factor * 0.50
        + product_factor * 0.50
    )

    impact_score = base_score * status_multiplier
    impact_score = max(0.0, min(100.0, impact_score))

    if impact_score >= 80:
        impact_level = "critical"
    elif impact_score >= 60:
        impact_level = "high"
    elif impact_score >= 35:
        impact_level = "medium"
    else:
        impact_level = "low"

    # Delay estimate derived from impact severity.
    if impact_score >= 80:
        estimated_delay_days = 14
    elif impact_score >= 60:
        estimated_delay_days = 7
    elif impact_score >= 35:
        estimated_delay_days = 3
    else:
        estimated_delay_days = 1

    supplier_impact_score = min(
        100.0,
        impact_score + supplier_factor,
    )

    product_impact_score = min(
        100.0,
        impact_score + product_factor,
    )

    explanation = (
        f"Impact is {impact_level} with a score of "
        f"{impact_score:.1f}/100. "
        f"The estimate considers event type, severity, "
        f"event status, affected suppliers, and affected products."
    )

    return ImpactResult(
        impact_score=round(impact_score, 2),
        impact_level=impact_level,
        estimated_delay_days=estimated_delay_days,
        supplier_impact_score=round(supplier_impact_score, 2),
        product_impact_score=round(product_impact_score, 2),
        explanation=explanation,
    )


def calculate_event_impact(
    event: Any,
    *,
    supplier_count: int = 0,
    product_count: int = 0,
) -> dict[str, Any]:
    """
    Convenience wrapper for SQLAlchemy Event objects.
    """

    result = calculate_impact(
        event_type=getattr(event, "event_type", None),
        severity=getattr(event, "severity", None),
        status=getattr(event, "status", None),
        supplier_count=supplier_count,
        product_count=product_count,
    )

    return {
        "event_id": getattr(event, "id", None),
        "title": getattr(event, "title", None),
        "impact_score": result.impact_score,
        "impact_level": result.impact_level,
        "estimated_delay_days": result.estimated_delay_days,
        "supplier_impact_score": result.supplier_impact_score,
        "product_impact_score": result.product_impact_score,
        "explanation": result.explanation,
    }
