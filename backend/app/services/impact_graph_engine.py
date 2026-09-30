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
    Build an impact graph using actual AtmoGraph
    event, supplier, product and relationship data.
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

    event_ids = {
        relationship.event_id
        for relationship in relationships
    }

    supplier_ids = {
        relationship.supplier_id
        for relationship in relationships
    }

    product_ids = {
        relationship.product_id
        for relationship in relationships
    }

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

    nodes = []
    edges = []

    for event in events:
        nodes.append(
            {
                "id": f"event-{event.id}",
                "type": "event",
                "label": event.title,
                "event_id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "status": event.status,
                "location": event.location,
            }
        )

    for supplier in suppliers:
        nodes.append(
            {
                "id": f"supplier-{supplier.id}",
                "type": "supplier",
                "label": supplier.name,
                "supplier_id": supplier.id,
                "country": supplier.country,
                "industry": supplier.industry,
            }
        )

    for product in products:
        nodes.append(
            {
                "id": f"product-{product.id}",
                "type": "product",
                "label": product.name,
                "product_id": product.id,
                "category": product.category,
            }
        )

    for relationship in relationships:
        event_node = f"event-{relationship.event_id}"
        supplier_node = f"supplier-{relationship.supplier_id}"
        product_node = f"product-{relationship.product_id}"

        delay_days = relationship.estimated_delay_days or 0

        edges.append(
            {
                "id": f"relationship-{relationship.id}-supplier",
                "source": event_node,
                "target": supplier_node,
                "relationship_type": relationship.relationship_type,
                "impact_level": relationship.impact_level,
                "estimated_delay_days": delay_days,
            }
        )

        edges.append(
            {
                "id": f"relationship-{relationship.id}-product",
                "source": supplier_node,
                "target": product_node,
                "relationship_type": "supplies",
                "impact_level": relationship.impact_level,
                "estimated_delay_days": delay_days,
            }
        )

    return {
        "event_id": event_id,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "event_count": len(events),
            "supplier_count": len(suppliers),
            "product_count": len(products),
        },
    }