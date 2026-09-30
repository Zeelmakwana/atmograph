from sqlalchemy.orm import Session

from app.models import (
    Event,
    Supplier,
    Product,
    SupplyChainLink,
)


def build_impact_graph(
    db: Session,
    event_id: int | None = None,
) -> dict:
    """
    Build a graph representation from the actual
    AtmoGraph supply-chain relationships.
    """

    query = db.query(SupplyChainLink)

    if event_id is not None:
        query = query.filter(
            SupplyChainLink.event_id == event_id
        )

    relationships = query.all()

    if event_id is not None:
        event = (
            db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if event is None:
            return None

    nodes = {}
    edges = []

    event_ids = set()
    supplier_ids = set()
    product_ids = set()

    for relationship in relationships:
        event_ids.add(relationship.event_id)
        supplier_ids.add(relationship.supplier_id)
        product_ids.add(relationship.product_id)

    events = (
        db.query(Event)
        .filter(Event.id.in_(event_ids))
        .all()
        if event_ids
        else []
    )

    suppliers = (
        db.query(Supplier)
        .filter(Supplier.id.in_(supplier_ids))
        .all()
        if supplier_ids
        else []
    )

    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .all()
        if product_ids
        else []
    )

    for event in events:
        node_id = f"event-{event.id}"

        nodes[node_id] = {
            "id": node_id,
            "type": "event",
            "label": event.title,
            "event_id": event.id,
            "event_type": event.event_type,
            "severity": event.severity,
            "status": event.status,
            "location": event.location,
        }

    for supplier in suppliers:
        node_id = f"supplier-{supplier.id}"

        nodes[node_id] = {
            "id": node_id,
            "type": "supplier",
            "label": supplier.name,
            "supplier_id": supplier.id,
            "country": supplier.country,
            "industry": supplier.industry,
        }

    for product in products:
        node_id = f"product-{product.id}"

        nodes[node_id] = {
            "id": node_id,
            "type": "product",
            "label": product.name,
            "product_id": product.id,
            "category": product.category,
        }

    for relationship in relationships:
        event_node = f"event-{relationship.event_id}"
        supplier_node = f"supplier-{relationship.supplier_id}"
        product_node = f"product-{relationship.product_id}"

        edges.append(
            {
                "id": f"relationship-{relationship.id}-supplier",
                "source": event_node,
                "target": supplier_node,
                "relationship_type": relationship.relationship_type,
                "impact_level": relationship.impact_level,
                "estimated_delay_days": (
                    relationship.estimated_delay_days or 0
                ),
            }
        )

        edges.append(
            {
                "id": f"relationship-{relationship.id}-product",
                "source": supplier_node,
                "target": product_node,
                "relationship_type": "supplies",
                "impact_level": relationship.impact_level,
                "estimated_delay_days": (
                    relationship.estimated_delay_days or 0
                ),
            }
        )

    return {
        "event_id": event_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "event_count": len(events),
            "supplier_count": len(suppliers),
            "product_count": len(products),
        },
    }

def predict_event_impact(
    db: Session,
    event_id: int,
) -> dict:
    """
    Generate a supply-chain impact prediction for one event.

    Uses the actual event and its supply-chain relationships
    to calculate affected suppliers, products, delay, and risk.
    """

    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if event is None:
        return None

    relationships = (
        db.query(SupplyChainLink)
        .filter(SupplyChainLink.event_id == event_id)
        .all()
    )

    supplier_ids = {
        relationship.supplier_id
        for relationship in relationships
    }

    product_ids = {
        relationship.product_id
        for relationship in relationships
    }

    suppliers = (
        db.query(Supplier)
        .filter(Supplier.id.in_(supplier_ids))
        .all()
        if supplier_ids
        else []
    )

    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .all()
        if product_ids
        else []
    )

    severity = str(event.severity).strip().lower()

    severity_score = {
        "critical": 100,
        "very_high": 90,
        "high": 80,
        "severe": 80,
        "5": 100,
        "4": 80,
        "3": 60,
        "medium": 60,
        "moderate": 60,
        "2": 40,
        "low": 30,
        "minor": 30,
        "1": 20,
    }.get(severity, 50)

    status = str(event.status).strip().lower()

    if status == "active":
        status_multiplier = 1.0
    elif status in {"resolved", "closed"}:
        status_multiplier = 0.4
    else:
        status_multiplier = 0.7

    supplier_factor = min(len(suppliers) * 5, 20)
    product_factor = min(len(products) * 5, 20)

    risk_score = (
        severity_score * 0.6
        + supplier_factor
        + product_factor
    ) * status_multiplier

    risk_score = round(
        max(0.0, min(100.0, risk_score)),
        2,
    )

    if risk_score >= 75:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    total_delay = sum(
        relationship.estimated_delay_days or 0
        for relationship in relationships
    )

    if relationships:
        estimated_delay_days = round(
            total_delay / len(relationships)
        )
    else:
        estimated_delay_days = 0

    affected_supplier_names = [
        supplier.name
        for supplier in suppliers
    ]

    affected_product_names = [
        product.name
        for product in products
    ]

    impacts = []

    for supplier in suppliers:
        impacts.append(
            {
                "entity_type": "supplier",
                "entity_name": supplier.name,
                "impact_type": "supply_disruption",
                "severity": risk_level,
                "probability": round(
                    min(1.0, risk_score / 100),
                    2,
                ),
                "estimated_delay_days": estimated_delay_days,
            }
        )

    for product in products:
        impacts.append(
            {
                "entity_type": "product",
                "entity_name": product.name,
                "impact_type": "availability_risk",
                "severity": risk_level,
                "probability": round(
                    min(1.0, risk_score / 100),
                    2,
                ),
                "estimated_delay_days": estimated_delay_days,
            }
        )

    explanation = [
        f"Event severity is {event.severity}.",
        f"Event status is {event.status}.",
        f"{len(suppliers)} suppliers are directly affected.",
        f"{len(products)} products are directly affected.",
        f"Estimated average delay is {estimated_delay_days} days.",
    ]

    return {
        "event_id": event.id,
        "event_title": event.title,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "primary_impact": (
            "Supply chain disruption"
            if relationships
            else "Limited direct impact identified"
        ),
        "affected_regions": (
            [event.location]
            if event.location
            else []
        ),
        "affected_products": affected_product_names,
        "affected_suppliers": affected_supplier_names,
        "impacts": impacts,
        "explanation": explanation,
    }