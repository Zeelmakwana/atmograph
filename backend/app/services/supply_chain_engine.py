from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import (
    Event,
    Product,
    Supplier,
    SupplyChainLink,
)


@dataclass
class SupplyChainImpactResult:
    event_id: int
    event_title: str

    risk_score: float
    risk_level: str

    primary_impact: str

    affected_regions: list[str]
    affected_products: list[str]
    affected_suppliers: list[str]

    impacts: list[dict]

    explanation: list[str]

    supplier_count: int
    product_count: int
    relationship_count: int


def _severity_score(severity: str | int | None) -> float:
    """
    Convert event severity into a normalized score.
    """

    if severity is None:
        return 40.0

    if isinstance(severity, int):
        return float(max(0, min(severity, 100)))

    value = str(severity).strip().lower()

    mapping = {
        "low": 25.0,
        "medium": 50.0,
        "moderate": 55.0,
        "high": 80.0,
        "critical": 100.0,
        "severe": 90.0,
    }

    return mapping.get(value, 50.0)


def _event_type_score(event_type: str | None) -> float:
    """
    Estimate how strongly an event type can affect a supply chain.
    """

    if not event_type:
        return 50.0

    value = event_type.strip().lower()

    scores = {
        "port_strike": 90.0,
        "port_closure": 95.0,
        "supply_chain_disruption": 85.0,
        "shipping_disruption": 85.0,
        "transport_disruption": 80.0,
        "weather_disruption": 75.0,
        "natural_disaster": 95.0,
        "geopolitical": 90.0,
        "war": 100.0,
        "sanction": 85.0,
        "factory_shutdown": 90.0,
        "supplier_failure": 90.0,
        "cyber_attack": 85.0,
        "labor_strike": 75.0,
    }

    return scores.get(value, 60.0)


def _status_multiplier(status: str | None) -> float:
    """
    Active events have a stronger immediate impact.
    """

    if not status:
        return 1.0

    value = status.strip().lower()

    mapping = {
        "active": 1.00,
        "ongoing": 1.00,
        "escalating": 1.10,
        "critical": 1.15,
        "resolved": 0.35,
        "closed": 0.25,
        "inactive": 0.40,
        "cancelled": 0.20,
    }

    return mapping.get(value, 0.85)


def _risk_level(score: float) -> str:
    if score >= 80:
        return "critical"

    if score >= 60:
        return "high"

    if score >= 35:
        return "medium"

    return "low"


def _impact_type(event: Event) -> str:
    """
    Convert event type into a human-readable supply-chain impact.
    """

    event_type = (event.event_type or "").lower()

    if "port" in event_type:
        return "shipping_delay"

    if "weather" in event_type:
        return "transport_disruption"

    if "supplier" in event_type:
        return "supplier_disruption"

    if "factory" in event_type:
        return "production_delay"

    if "cyber" in event_type:
        return "operational_disruption"

    if "sanction" in event_type or "geopolitical" in event_type:
        return "trade_disruption"

    if "strike" in event_type:
        return "logistics_disruption"

    return "supply_chain_disruption"


def _probability(
    risk_score: float,
    impact_level: str,
) -> float:
    """
    Convert risk score into a probability value between 0 and 1.
    """

    if impact_level == "critical":
        probability = 0.90

    elif impact_level == "high":
        probability = 0.75

    elif impact_level == "medium":
        probability = 0.55

    else:
        probability = 0.30

    score_adjustment = (risk_score - 50.0) / 500.0

    probability += score_adjustment

    return round(
        max(0.0, min(probability, 1.0)),
        2,
    )


def _estimated_delay_days(
    risk_score: float,
    relationship_count: int,
) -> int:
    """
    Estimate disruption duration.

    More severe events and more affected relationships
    increase the expected delay.
    """

    if risk_score >= 85:
        base_delay = 10

    elif risk_score >= 70:
        base_delay = 7

    elif risk_score >= 50:
        base_delay = 4

    elif risk_score >= 30:
        base_delay = 2

    else:
        base_delay = 1

    relationship_bonus = min(
        max(relationship_count - 1, 0) // 2,
        5,
    )

    return base_delay + relationship_bonus


def get_event_supply_chain_impact(
    db: Session,
    event: Event,
) -> SupplyChainImpactResult:
    """
    Calculate supply-chain impact for an event.

    Flow:

        Event
          ↓
        SupplyChainLink
          ↓
        Supplier
          ↓
        Product
          ↓
        Impact calculation
          ↓
        Prediction response
    """

    links = (
        db.query(SupplyChainLink)
        .filter(
            SupplyChainLink.event_id == event.id
        )
        .all()
    )

    suppliers: list[Supplier] = []
    products: list[Product] = []

    supplier_ids: set[int] = set()
    product_ids: set[int] = set()

    for link in links:

        if link.supplier_id not in supplier_ids:
            supplier = (
                db.query(Supplier)
                .filter(
                    Supplier.id == link.supplier_id
                )
                .first()
            )

            if supplier is not None:
                suppliers.append(supplier)
                supplier_ids.add(supplier.id)

        if link.product_id not in product_ids:
            product = (
                db.query(Product)
                .filter(
                    Product.id == link.product_id
                )
                .first()
            )

            if product is not None:
                products.append(product)
                product_ids.add(product.id)

    supplier_count = len(suppliers)
    product_count = len(products)
    relationship_count = len(links)

    severity_score = _severity_score(
        event.severity
    )

    event_type_score = _event_type_score(
        event.event_type
    )

    status_multiplier = _status_multiplier(
        event.status
    )

    relationship_factor = min(
        relationship_count * 2.5,
        15.0,
    )

    supplier_factor = min(
        supplier_count * 3.0,
        15.0,
    )

    product_factor = min(
        product_count * 2.0,
        10.0,
    )

    raw_score = (
        severity_score * 0.35
        + event_type_score * 0.35
        + relationship_factor
        + supplier_factor
        + product_factor
    )

    risk_score = raw_score * status_multiplier

    risk_score = round(
        max(0.0, min(risk_score, 100.0)),
        2,
    )

    risk_level = _risk_level(
        risk_score
    )

    primary_impact = _impact_type(
        event
    )

    probability = _probability(
        risk_score,
        risk_level,
    )

    estimated_delay_days = _estimated_delay_days(
        risk_score,
        relationship_count,
    )

    affected_regions: list[str] = []

    if event.location:
        affected_regions.append(
            event.location
        )

    for supplier in suppliers:
        if supplier.country:
            if supplier.country not in affected_regions:
                affected_regions.append(
                    supplier.country
                )

    impacts: list[dict] = []

    for product in products:

        impacts.append(
            {
                "entity_type": "product",
                "entity_name": product.name,
                "impact_type": primary_impact,
                "severity": risk_level,
                "probability": probability,
                "estimated_delay_days": estimated_delay_days,
            }
        )

    for supplier in suppliers:

        impacts.append(
            {
                "entity_type": "supplier",
                "entity_name": supplier.name,
                "impact_type": primary_impact,
                "severity": risk_level,
                "probability": probability,
                "estimated_delay_days": estimated_delay_days,
            }
        )

    explanation: list[str] = []

    explanation.append(
        f"Event '{event.title}' has a "
        f"{risk_level} supply-chain impact."
    )

    explanation.append(
        f"Calculated impact score is "
        f"{risk_score}/100."
    )

    explanation.append(
        f"The event is linked to "
        f"{supplier_count} supplier(s) and "
        f"{product_count} product(s)."
    )

    if relationship_count > 0:
        explanation.append(
            f"{relationship_count} explicit "
            f"supply-chain relationship(s) were "
            f"used in the calculation."
        )
    else:
        explanation.append(
            "No explicit supply-chain relationships "
            "are currently attached to this event."
        )

    explanation.append(
        f"Estimated disruption delay is "
        f"{estimated_delay_days} day(s)."
    )

    return SupplyChainImpactResult(
        event_id=event.id,
        event_title=event.title,
        risk_score=risk_score,
        risk_level=risk_level,
        primary_impact=primary_impact,
        affected_regions=affected_regions,
        affected_products=[
            product.name
            for product in products
        ],
        affected_suppliers=[
            supplier.name
            for supplier in suppliers
        ],
        impacts=impacts,
        explanation=explanation,
        supplier_count=supplier_count,
        product_count=product_count,
        relationship_count=relationship_count,
    )