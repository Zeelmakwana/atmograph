from collections import Counter

from sqlalchemy.orm import Session

from app.models import Event, Supplier, Product, SupplyChainLink
from app.services.risk_engine import calculate_risk


def _severity_level(severity) -> str:
    """
    Normalize both numeric and string severity values.
    """

    if severity is None:
        return "unknown"

    if isinstance(severity, str):
        value = severity.strip().lower()

        if value in {"critical", "very_high"}:
            return "high"

        if value in {"high", "severe"}:
            return "high"

        if value in {"medium", "moderate"}:
            return "medium"

        if value in {"low", "minor"}:
            return "low"

        try:
            severity = int(value)
        except ValueError:
            return "unknown"

    if isinstance(severity, (int, float)):
        if severity >= 4:
            return "high"

        if severity == 3:
            return "medium"

        if severity <= 2:
            return "low"

    return "unknown"


def build_dashboard_summary(db: Session) -> dict:
    events = db.query(Event).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()
    relationships = db.query(SupplyChainLink).all()

    total_events = len(events)
    total_suppliers = len(suppliers)
    total_products = len(products)
    total_relationships = len(relationships)

    active_events = sum(
        1
        for event in events
        if event.status
        and str(event.status).strip().lower() == "active"
    )

    severity_counts = Counter()

    for event in events:
        level = _severity_level(event.severity)
        severity_counts[level] += 1

    event_type_counts = Counter(
        event.event_type
        for event in events
        if event.event_type
    )

    location_counts = Counter(
        event.location
        for event in events
        if event.location
    )

    total_delay_days = sum(
        relationship.estimated_delay_days or 0
        for relationship in relationships
    )

    affected_supplier_ids = {
        relationship.supplier_id
        for relationship in relationships
    }

    affected_product_ids = {
        relationship.product_id
        for relationship in relationships
    }

    return {
        "overview": {
            "total_events": total_events,
            "active_events": active_events,
            "total_suppliers": total_suppliers,
            "total_products": total_products,
            "total_relationships": total_relationships,
            "affected_suppliers": len(affected_supplier_ids),
            "affected_products": len(affected_product_ids),
            "estimated_total_delay_days": total_delay_days,
        },

        "risk_distribution": {
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "unknown": severity_counts["unknown"],
        },

        "event_types": [
            {
                "event_type": event_type,
                "count": count,
            }
            for event_type, count in event_type_counts.most_common()
        ],

        "locations": [
            {
                "location": location,
                "count": count,
            }
            for location, count in location_counts.most_common()
        ],
    }

def build_event_analytics(db: Session) -> dict:
    events = db.query(Event).all()

    severity_counts = Counter()
    status_counts = Counter()
    event_type_counts = Counter()
    location_counts = Counter()

    for event in events:
        severity_counts[_severity_level(event.severity)] += 1

        if event.status:
            status_counts[str(event.status).strip().lower()] += 1

        if event.event_type:
            event_type_counts[event.event_type] += 1

        if event.location:
            location_counts[event.location] += 1

    return {
        "total_events": len(events),

        "severity_distribution": {
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "unknown": severity_counts["unknown"],
        },

        "status_distribution": dict(
            status_counts.most_common()
        ),

        "event_type_distribution": [
            {
                "event_type": event_type,
                "count": count,
            }
            for event_type, count
            in event_type_counts.most_common()
        ],

        "location_distribution": [
            {
                "location": location,
                "count": count,
            }
            for location, count
            in location_counts.most_common()
        ],
    }

def build_impact_analytics(db: Session) -> dict:
    relationships = db.query(SupplyChainLink).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()
    events = db.query(Event).all()

    supplier_map = {
        supplier.id: supplier
        for supplier in suppliers
    }

    product_map = {
        product.id: product
        for product in products
    }

    event_map = {
        event.id: event
        for event in events
    }

    supplier_stats = {}
    product_stats = {}
    event_stats = {}

    for relationship in relationships:
        delay = relationship.estimated_delay_days or 0

        supplier = supplier_map.get(relationship.supplier_id)
        product = product_map.get(relationship.product_id)
        event = event_map.get(relationship.event_id)

        if supplier:
            if supplier.id not in supplier_stats:
                supplier_stats[supplier.id] = {
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.name,
                    "country": supplier.country,
                    "relationship_count": 0,
                    "total_delay_days": 0,
                }

            supplier_stats[supplier.id]["relationship_count"] += 1
            supplier_stats[supplier.id]["total_delay_days"] += delay

        if product:
            if product.id not in product_stats:
                product_stats[product.id] = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "relationship_count": 0,
                    "total_delay_days": 0,
                }

            product_stats[product.id]["relationship_count"] += 1
            product_stats[product.id]["total_delay_days"] += delay

        if event:
            if event.id not in event_stats:
                event_stats[event.id] = {
                    "event_id": event.id,
                    "event_title": event.title,
                    "event_type": event.event_type,
                    "severity": _severity_level(event.severity),
                    "relationship_count": 0,
                    "total_delay_days": 0,
                }

            event_stats[event.id]["relationship_count"] += 1
            event_stats[event.id]["total_delay_days"] += delay

    supplier_results = sorted(
        supplier_stats.values(),
        key=lambda item: item["total_delay_days"],
        reverse=True,
    )

    product_results = sorted(
        product_stats.values(),
        key=lambda item: item["total_delay_days"],
        reverse=True,
    )

    event_results = sorted(
        event_stats.values(),
        key=lambda item: item["total_delay_days"],
        reverse=True,
    )

    return {
        "suppliers": supplier_results,
        "products": product_results,
        "events": event_results,
        "summary": {
            "suppliers_affected": len(supplier_results),
            "products_affected": len(product_results),
            "events_with_impact": len(event_results),
            "total_relationships": len(relationships),
            "total_estimated_delay_days": sum(
                item["total_delay_days"]
                for item in supplier_results
            ),
        },
    }

def build_top_affected_entities(db: Session) -> dict:
    relationships = db.query(SupplyChainLink).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()

    supplier_map = {
        supplier.id: supplier.name
        for supplier in suppliers
    }

    product_map = {
        product.id: product.name
        for product in products
    }

    supplier_impact = Counter()
    product_impact = Counter()

    supplier_delays = Counter()
    product_delays = Counter()

    for relationship in relationships:
        delay = relationship.estimated_delay_days or 0

        if relationship.supplier_id in supplier_map:
            supplier_impact[relationship.supplier_id] += 1
            supplier_delays[relationship.supplier_id] += delay

        if relationship.product_id in product_map:
            product_impact[relationship.product_id] += 1
            product_delays[relationship.product_id] += delay

    top_suppliers = []

    for supplier_id, count in supplier_impact.most_common():
        top_suppliers.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_map[supplier_id],
                "impact_count": count,
                "estimated_delay_days": supplier_delays[supplier_id],
            }
        )

    top_products = []

    for product_id, count in product_impact.most_common():
        top_products.append(
            {
                "product_id": product_id,
                "product_name": product_map[product_id],
                "impact_count": count,
                "estimated_delay_days": product_delays[product_id],
            }
        )

    return {
        "top_suppliers": top_suppliers[:10],
        "top_products": top_products[:10],
    }

def build_risk_overview(db: Session) -> dict:
    events = db.query(Event).all()

    risk_scores = []
    risk_events = []

    for event in events:
        result = calculate_risk(
            event_type=event.event_type,
            severity=event.severity,
            status=event.status,
        )

        risk_score = float(result["risk_score"])
        risk_level = result["risk_level"]

        risk_scores.append(risk_score)

        risk_events.append(
            {
                "event_id": event.id,
                "event_title": event.title,
                "event_type": event.event_type,
                "risk_score": risk_score,
                "risk_level": risk_level,
            }
        )

    high_risk = [
        item for item in risk_events
        if str(item["risk_level"]).lower() == "high"
    ]

    medium_risk = [
        item for item in risk_events
        if str(item["risk_level"]).lower() == "medium"
    ]

    low_risk = [
        item for item in risk_events
        if str(item["risk_level"]).lower() == "low"
    ]

    average_risk = (
        sum(risk_scores) / len(risk_scores)
        if risk_scores
        else 0.0
    )

    highest_risk_event = (
        max(risk_events, key=lambda item: item["risk_score"])
        if risk_events
        else None
    )

    return {
        "total_events": len(events),
        "high_risk_events": len(high_risk),
        "medium_risk_events": len(medium_risk),
        "low_risk_events": len(low_risk),
        "average_risk_score": round(average_risk, 2),
        "highest_risk_event": highest_risk_event,
        "events": sorted(
            risk_events,
            key=lambda item: item["risk_score"],
            reverse=True,
        ),
    }

def build_event_intelligence(db: Session) -> list[dict]:
    events = db.query(Event).order_by(Event.id.desc()).all()

    relationships = db.query(SupplyChainLink).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()

    supplier_map = {
        supplier.id: supplier.name
        for supplier in suppliers
    }

    product_map = {
        product.id: product.name
        for product in products
    }

    relationships_by_event = {}

    for relationship in relationships:
        relationships_by_event.setdefault(
            relationship.event_id,
            [],
        ).append(relationship)

    results = []

    for event in events:
        risk = calculate_risk(
            event_type=event.event_type,
            severity=event.severity,
            status=event.status,
        )

        event_relationships = relationships_by_event.get(
            event.id,
            [],
        )

        supplier_ids = {
            relationship.supplier_id
            for relationship in event_relationships
        }

        product_ids = {
            relationship.product_id
            for relationship in event_relationships
        }

        total_delay = sum(
            relationship.estimated_delay_days or 0
            for relationship in event_relationships
        )

        impact_levels = Counter(
            str(relationship.impact_level).lower()
            for relationship in event_relationships
            if relationship.impact_level
        )

        results.append(
            {
                "event_id": event.id,
                "event_title": event.title,
                "event_type": event.event_type,
                "location": event.location,
                "severity": _severity_level(event.severity),
                "status": event.status,

                "risk": {
                    "score": float(risk["risk_score"]),
                    "level": risk["risk_level"],
                },

                "supply_chain_impact": {
                    "affected_suppliers": len(supplier_ids),
                    "affected_products": len(product_ids),
                    "relationship_count": len(event_relationships),
                    "estimated_delay_days": total_delay,
                    "impact_distribution": dict(
                        impact_levels
                    ),
                },

                "suppliers": [
                    supplier_map[supplier_id]
                    for supplier_id in supplier_ids
                    if supplier_id in supplier_map
                ],

                "products": [
                    product_map[product_id]
                    for product_id in product_ids
                    if product_id in product_map
                ],
            }
        )

    return results

def build_graph_intelligence(db: Session) -> dict:
    events = db.query(Event).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()
    relationships = db.query(SupplyChainLink).all()

    nodes = []
    edges = []

    for event in events:
        risk = calculate_risk(
            event_type=event.event_type,
            severity=event.severity,
            status=event.status,
        )

        nodes.append(
            {
                "id": f"event_{event.id}",
                "type": "event",
                "label": event.title,
                "event_type": event.event_type,
                "location": event.location,
                "risk_score": float(risk["risk_score"]),
                "risk_level": risk["risk_level"],
            }
        )

    for supplier in suppliers:
        nodes.append(
            {
                "id": f"supplier_{supplier.id}",
                "type": "supplier",
                "label": supplier.name,
                "country": supplier.country,
                "industry": supplier.industry,
            }
        )

    for product in products:
        nodes.append(
            {
                "id": f"product_{product.id}",
                "type": "product",
                "label": product.name,
                "category": product.category,
            }
        )

    for relationship in relationships:
        edges.append(
            {
                "id": f"relationship_{relationship.id}",
                "source": f"event_{relationship.event_id}",
                "target": f"supplier_{relationship.supplier_id}",
                "product_id": relationship.product_id,
                "relationship_type": relationship.relationship_type,
                "impact_level": relationship.impact_level,
                "estimated_delay_days": (
                    relationship.estimated_delay_days or 0
                ),
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "event_nodes": len(events),
            "supplier_nodes": len(suppliers),
            "product_nodes": len(products),
        },
    }

def build_impact_graph(db: Session) -> dict:
    events = db.query(Event).all()
    suppliers = db.query(Supplier).all()
    products = db.query(Product).all()
    relationships = db.query(SupplyChainLink).all()

    nodes = []
    edges = []

    for event in events:
        risk = calculate_risk(
            event_type=event.event_type,
            severity=event.severity,
            status=event.status,
        )

        nodes.append(
            {
                "id": f"event_{event.id}",
                "type": "event",
                "label": event.title,
                "risk_score": float(risk["risk_score"]),
                "risk_level": risk["risk_level"],
                "location": event.location,
            }
        )

    for supplier in suppliers:
        nodes.append(
            {
                "id": f"supplier_{supplier.id}",
                "type": "supplier",
                "label": supplier.name,
                "country": supplier.country,
                "industry": supplier.industry,
            }
        )

    for product in products:
        nodes.append(
            {
                "id": f"product_{product.id}",
                "type": "product",
                "label": product.name,
                "category": product.category,
            }
        )

    for relationship in relationships:
        delay = relationship.estimated_delay_days or 0

        edges.append(
            {
                "id": f"event_supplier_{relationship.id}",
                "source": f"event_{relationship.event_id}",
                "target": f"supplier_{relationship.supplier_id}",
                "type": "event_to_supplier",
                "relationship_type": relationship.relationship_type,
                "impact_level": relationship.impact_level,
                "estimated_delay_days": delay,
            }
        )

        edges.append(
            {
                "id": f"supplier_product_{relationship.id}",
                "source": f"supplier_{relationship.supplier_id}",
                "target": f"product_{relationship.product_id}",
                "type": "supplier_to_product",
                "relationship_type": "supplies",
                "impact_level": relationship.impact_level,
                "estimated_delay_days": delay,
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "events": len(events),
            "suppliers": len(suppliers),
            "products": len(products),
            "relationships": len(relationships),
        },
    }