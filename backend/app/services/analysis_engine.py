from sqlalchemy.orm import Session

from app.models import Event, SupplyChainLink
from app.services.risk_engine import calculate_risk
from app.services.supply_chain_engine import get_event_supply_chain_impact


def analyze_event(
    event: Event,
    db: Session,
) -> dict:
    """
    Build a unified analysis for a supply-chain event.

    Combines:
    - Risk analysis
    - Supply-chain impact
    - Affected suppliers
    - Affected products
    - Affected regions
    """

    # ---------------------------------------------------------
    # RISK
    # ---------------------------------------------------------

    risk = calculate_risk(
        event_type=event.event_type,
        severity=event.severity,
        status=event.status,
    )

    # ---------------------------------------------------------
    # SUPPLY CHAIN IMPACT
    # ---------------------------------------------------------

    impact = get_event_supply_chain_impact(
        event=event,
        db=db,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------

    links = (
        db.query(SupplyChainLink)
        .filter(
            SupplyChainLink.event_id == event.id
        )
        .all()
    )

    suppliers = []
    products = []

    for link in links:
        if link.supplier is not None:
            suppliers.append(link.supplier.name)

        if link.product is not None:
            products.append(link.product.name)

    # Remove duplicates while preserving order
    suppliers = list(dict.fromkeys(suppliers))
    products = list(dict.fromkeys(products))

    # ---------------------------------------------------------
    # REGION
    # ---------------------------------------------------------

    regions = []

    if event.location:
        regions.append(event.location)

    regions = list(dict.fromkeys(regions))

    estimated_delay_days = max(
        (
            item["estimated_delay_days"]
            for item in impact.impacts
        ),
        default=0,
    )

    # ---------------------------------------------------------
    # EXPLANATION
    # ---------------------------------------------------------

    explanation = [
        (
            f"Event '{event.title}' has a "
            f"{risk['risk_level']} risk level with a "
            f"risk score of {risk['risk_score']:.1f}/100."
        ),
        (
            f"Estimated supply-chain impact is "
            f"{impact.risk_level} with an "
            f"impact score of {impact.risk_score:.1f}/100."
        ),
        (
            f"The event affects {len(suppliers)} supplier(s) "
            f"and {len(products)} product(s)."
        ),
        (
            f"Estimated disruption delay is "
            f"{estimated_delay_days} day(s)."
        ),
    ]

    if regions:
        explanation.append(
            f"Primary affected region: {regions[0]}."
        )

    return {
        "event_id": event.id,
        "event_title": event.title,

        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],

        "impact_score": impact.risk_score,
        "impact_level": impact.risk_level,

        "estimated_delay_days": estimated_delay_days,

        "supplier_count": len(suppliers),
        "product_count": len(products),

        "affected_regions": regions,
        "affected_suppliers": suppliers,
        "affected_products": products,

        "explanation": explanation,
    }
