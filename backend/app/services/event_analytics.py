from collections import Counter

from sqlalchemy.orm import Session

from app.models import (
    Event,
    Supplier,
    Product,
    SupplyChainLink,
)


def get_event_analytics(
    db: Session,
    event_id: int | None = None,
) -> dict:
    """
    Return aggregated analytics for all events or
    detailed analytics for a single event.
    """

    if event_id is not None:
        event = (
            db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if event is None:
            return None

        relationships = (
            db.query(SupplyChainLink)
            .filter(
                SupplyChainLink.event_id == event_id
            )
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

        total_delay = sum(
            relationship.estimated_delay_days or 0
            for relationship in relationships
        )

        impact_levels = Counter(
            relationship.impact_level
            for relationship in relationships
            if relationship.impact_level
        )

        relationship_types = Counter(
            relationship.relationship_type
            for relationship in relationships
            if relationship.relationship_type
        )

        return {
            "event": {
                "id": event.id,
                "title": event.title,
                "event_type": event.event_type,
                "severity": event.severity,
                "status": event.status,
                "location": event.location,
                "source": event.source,
            },
            "impact_summary": {
                "affected_suppliers": len(suppliers),
                "affected_products": len(products),
                "relationships": len(relationships),
                "estimated_total_delay_days": total_delay,
            },
            "suppliers": [
                {
                    "id": supplier.id,
                    "name": supplier.name,
                    "country": supplier.country,
                    "industry": supplier.industry,
                }
                for supplier in suppliers
            ],
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                }
                for product in products
            ],
            "impact_levels": dict(impact_levels),
            "relationship_types": dict(relationship_types),
            "relationships": [
                {
                    "id": relationship.id,
                    "supplier_id": relationship.supplier_id,
                    "product_id": relationship.product_id,
                    "relationship_type": relationship.relationship_type,
                    "impact_level": relationship.impact_level,
                    "estimated_delay_days": (
                        relationship.estimated_delay_days or 0
                    ),
                }
                for relationship in relationships
            ],
        }

    events = db.query(Event).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()
    relationships = db.query(SupplyChainLink).all()

    severity_distribution = Counter(
        str(event.severity)
        for event in events
        if event.severity is not None
    )

    status_distribution = Counter(
        str(event.status).strip().lower()
        for event in events
        if event.status
    )

    event_type_distribution = Counter(
        event.event_type
        for event in events
        if event.event_type
    )

    supplier_event_counts = Counter(
        relationship.supplier_id
        for relationship in relationships
    )

    product_event_counts = Counter(
        relationship.product_id
        for relationship in relationships
    )

    supplier_map = {
        supplier.id: supplier
        for supplier in suppliers
    }

    product_map = {
        product.id: product
        for product in products
    }

    top_suppliers = [
        {
            "supplier_id": supplier_id,
            "supplier_name": supplier_map[supplier_id].name,
            "affected_events": count,
        }
        for supplier_id, count in supplier_event_counts.most_common()
        if supplier_id in supplier_map
    ]

    top_products = [
        {
            "product_id": product_id,
            "product_name": product_map[product_id].name,
            "affected_events": count,
        }
        for product_id, count in product_event_counts.most_common()
        if product_id in product_map
    ]

    return {
        "total_events": len(events),
        "total_suppliers": len(suppliers),
        "total_products": len(products),
        "total_relationships": len(relationships),
        "severity_distribution": dict(severity_distribution),
        "status_distribution": dict(status_distribution),
        "event_type_distribution": dict(event_type_distribution),
        "top_affected_suppliers": top_suppliers,
        "top_affected_products": top_products,
    }