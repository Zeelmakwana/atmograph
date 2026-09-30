from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_engine import (
    build_dashboard_summary,
    build_event_analytics,
    build_impact_analytics,
    build_top_affected_entities,
    build_risk_overview,
    build_event_intelligence,
    build_graph_intelligence,
    build_impact_graph,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/",
    response_model=DashboardResponse,
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
):
    """
    Return aggregated AtmoGraph dashboard statistics.
    """
    return build_dashboard_summary(db)


@router.get(
    "/summary",
    response_model=DashboardResponse,
)
def get_dashboard_summary_detailed(
    db: Session = Depends(get_db),
):
    """
    Return aggregated AtmoGraph dashboard statistics.
    """
    return build_dashboard_summary(db)


@router.get(
    "/analytics",
)
def get_event_analytics(
    db: Session = Depends(get_db),
):
    """
    Return event analytics for the AtmoGraph dashboard.
    """
    return build_event_analytics(db)

@router.get(
    "/impact",
)
def get_impact_analytics(
    db: Session = Depends(get_db),
):
    """
    Return supplier, product, and event impact analytics.
    """
    return build_impact_analytics(db)

@router.get(
    "/top-affected",
)
def get_top_affected_entities(
    db: Session = Depends(get_db),
):
    """
    Return the most affected suppliers and products.
    """
    return build_top_affected_entities(db)

@router.get(
    "/risk-overview",
)
def get_risk_overview(
    db: Session = Depends(get_db),
):
    """
    Return risk distribution and highest-risk events.
    """
    return build_risk_overview(db)

@router.get(
    "/event-intelligence",
)
def get_event_intelligence(
    db: Session = Depends(get_db),
):
    """
    Return combined risk and supply-chain intelligence
    for every stored event.
    """
    return build_event_intelligence(db)

@router.get(
    "/graph-intelligence",
)
def get_graph_intelligence(
    db: Session = Depends(get_db),
):
    """
    Return an enriched supply-chain graph with
    risk and impact metadata.
    """
    return build_graph_intelligence(db)

@router.get(
    "/impact-graph",
)
def get_impact_graph(
    db: Session = Depends(get_db),
):
    """
    Return the complete Event -> Supplier -> Product
    impact graph.
    """
    return build_impact_graph(db)