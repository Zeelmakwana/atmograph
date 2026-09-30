from sqlalchemy.orm import Session

from app.services.prediction_engine import predict_event_impact


def build_ripple_graph(
    db: Session,
    event_id: int,
) -> dict:
    """
    Build a ripple-effect graph for a specific event.

    The graph is generated from the prediction engine output
    and represents the event, location, suppliers, products,
    and predicted impacts.
    """

    prediction = predict_event_impact(
        db=db,
        event_id=event_id,
    )

    if prediction is None:
        return None

    nodes = []
    edges = []

    node_ids = set()
    edge_ids = set()

    def add_node(
        node_id: str,
        node_type: str,
        label: str,
        data: dict | None = None,
    ):
        if node_id in node_ids:
            return

        nodes.append(
            {
                "id": node_id,
                "type": node_type,
                "label": label,
                "data": data or {},
            }
        )

        node_ids.add(node_id)

    def add_edge(
        edge_id: str,
        source: str,
        target: str,
        edge_type: str,
        label: str,
        data: dict | None = None,
    ):
        if edge_id in edge_ids:
            return

        edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "label": label,
                "data": data or {},
            }
        )

        edge_ids.add(edge_id)

    # ---------------------------------------------------------
    # EVENT NODE
    # ---------------------------------------------------------

    event_node_id = f"event-{prediction['event_id']}"

    add_node(
        node_id=event_node_id,
        node_type="event",
        label=prediction["event_title"],
        data={
            "event_id": prediction["event_id"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "primary_impact": prediction["primary_impact"],
        },
    )

    # ---------------------------------------------------------
    # REGION / LOCATION NODES
    # ---------------------------------------------------------

    for location in prediction["affected_regions"]:
        location_id = (
            f"location-{location.lower().replace(' ', '-')}"
        )

        add_node(
            node_id=location_id,
            node_type="location",
            label=location,
            data={
                "location": location,
            },
        )

        add_edge(
            edge_id=f"{event_node_id}-affects-{location_id}",
            source=event_node_id,
            target=location_id,
            edge_type="affects",
            label="affects",
        )

    # ---------------------------------------------------------
    # SUPPLIER NODES
    # ---------------------------------------------------------

    supplier_impacts = [
        impact
        for impact in prediction["impacts"]
        if impact["entity_type"] == "supplier"
    ]

    for supplier in prediction["affected_suppliers"]:
        supplier_id = (
            f"supplier-{supplier.lower().replace(' ', '-')}"
        )

        supplier_impact = next(
            (
                impact
                for impact in supplier_impacts
                if impact["entity_name"] == supplier
            ),
            None,
        )

        add_node(
            node_id=supplier_id,
            node_type="supplier",
            label=supplier,
            data={
                "supplier": supplier,
                "risk_level": prediction["risk_level"],
                "risk_score": prediction["risk_score"],
            },
        )

        add_edge(
            edge_id=f"{event_node_id}-disrupts-{supplier_id}",
            source=event_node_id,
            target=supplier_id,
            edge_type="disrupts",
            label="disrupts",
            data={
                "probability": (
                    supplier_impact["probability"]
                    if supplier_impact
                    else 0.0
                ),
                "estimated_delay_days": (
                    supplier_impact["estimated_delay_days"]
                    if supplier_impact
                    else 0
                ),
            },
        )

    # ---------------------------------------------------------
    # PRODUCT NODES
    # ---------------------------------------------------------

    product_impacts = [
        impact
        for impact in prediction["impacts"]
        if impact["entity_type"] == "product"
    ]

    for product in prediction["affected_products"]:
        product_id = (
            f"product-{product.lower().replace(' ', '-')}"
        )

        product_impact = next(
            (
                impact
                for impact in product_impacts
                if impact["entity_name"] == product
            ),
            None,
        )

        add_node(
            node_id=product_id,
            node_type="product",
            label=product,
            data={
                "product": product,
                "risk_level": prediction["risk_level"],
                "risk_score": prediction["risk_score"],
            },
        )

        add_edge(
            edge_id=f"{event_node_id}-impacts-{product_id}",
            source=event_node_id,
            target=product_id,
            edge_type="impacts",
            label="impacts",
            data={
                "probability": (
                    product_impact["probability"]
                    if product_impact
                    else 0.0
                ),
                "estimated_delay_days": (
                    product_impact["estimated_delay_days"]
                    if product_impact
                    else 0
                ),
            },
        )

    # ---------------------------------------------------------
    # IMPACT NODES
    # ---------------------------------------------------------

    for index, impact in enumerate(
        prediction["impacts"]
    ):
        impact_id = (
            f"impact-{prediction['event_id']}-{index}"
        )

        add_node(
            node_id=impact_id,
            node_type="impact",
            label=impact["impact_type"],
            data={
                "entity_type": impact["entity_type"],
                "entity_name": impact["entity_name"],
                "severity": impact["severity"],
                "probability": impact["probability"],
                "estimated_delay_days": (
                    impact["estimated_delay_days"]
                ),
            },
        )

        if impact["entity_type"] == "product":
            target_id = (
                f"product-"
                f"{impact['entity_name'].lower().replace(' ', '-')}"
            )
        else:
            target_id = (
                f"supplier-"
                f"{impact['entity_name'].lower().replace(' ', '-')}"
            )

        add_edge(
            edge_id=f"{target_id}-has-impact-{index}",
            source=target_id,
            target=impact_id,
            edge_type="has_impact",
            label="has impact",
            data={
                "probability": impact["probability"],
                "estimated_delay_days": (
                    impact["estimated_delay_days"]
                ),
            },
        )

    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    return {
        "event": {
            "id": prediction["event_id"],
            "title": prediction["event_title"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "primary_impact": prediction["primary_impact"],
        },
        "prediction": {
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "primary_impact": prediction["primary_impact"],
        },
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }