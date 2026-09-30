from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.services.neo4j_service import (
    Neo4jService,
)

from app.services.graph_features_service import (
    GraphFeaturesService,
)

from app.services.gnn_graph_service import (
    GNNGraphService,
)

from app.services.gnn_prediction_service import (
    GNNPredictionService,
)

from app.services.hybrid_prediction_service import (
    HybridPredictionService,
)

from app.services.event_impact_graph_service import (
    EventImpactGraphService,
)


router = APIRouter(
    prefix="/graph-intelligence",
    tags=["Graph Intelligence"],
)


# ============================================================
# GRAPH FEATURES
# ============================================================

@router.get("/features/{graph_id}")
def get_graph_features(
    graph_id: str,
):
    neo4j = Neo4jService()

    try:

        service = GraphFeaturesService(
            neo4j
        )

        result = service.extract_event_features(
            graph_id
        )

        if not result.get("success"):

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Unable to extract graph features.",
                ),
            )

        return result

    finally:

        neo4j.close()


# ============================================================
# GNN GRAPH
# ============================================================

@router.get("/gnn-graph/{graph_id}")
def get_gnn_graph(
    graph_id: str,
    max_depth: int = 3,
):
    neo4j = Neo4jService()

    try:

        service = GNNGraphService(
            neo4j
        )

        result = service.build_event_graph(
            graph_id=graph_id,
            max_depth=max_depth,
        )

        if not result.get("success"):

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Unable to build GNN graph.",
                ),
            )

        return result

    finally:

        neo4j.close()


# ============================================================
# GNN PREDICTION
# ============================================================

@router.get("/gnn-predict/{graph_id}")
def gnn_predict(
    graph_id: str,
):
    neo4j = Neo4jService()

    try:

        service = GNNPredictionService(
            neo4j
        )

        result = service.predict(
            graph_id
        )

        if not result.get("success"):

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "GNN prediction failed.",
                ),
            )

        return result

    finally:

        neo4j.close()


# ============================================================
# HYBRID PREDICTION
# ============================================================

@router.get(
    "/hybrid-predict/{event_id}/{graph_id}"
)
def hybrid_predict(
    event_id: int,
    graph_id: str,
    db: Session = Depends(get_db),
):

    service = HybridPredictionService()

    return service.predict(
        db=db,
        event_id=event_id,
        graph_id=graph_id,
    )


# ============================================================
# EVENT IMPACT GRAPH
# ============================================================

@router.get(
    "/event-impact/{event_id}"
)
def event_impact_graph(
    event_id: int,
    db: Session = Depends(get_db),
):
    """
    Build the operational business impact graph
    for a processed event.

    Event
      ↓
    Supplier
      ↓
    Component
      ↓
    Plant
      ↓
    Product
    """

    service = EventImpactGraphService(
        db
    )

    result = service.build(
        event_id
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=404,
            detail=result.get(
                "message",
                "Unable to build event impact graph.",
            ),
        )

    return result
