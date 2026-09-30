from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.impact_graph_engine import build_impact_graph


router = APIRouter(
    prefix="/impact-graph",
    tags=["Impact Graph"],
)


@router.get("/")
def get_impact_graph(
    db: Session = Depends(get_db),
):
    return build_impact_graph(db)


@router.get("/event/{event_id}")
def get_event_impact_graph(
    event_id: int,
    db: Session = Depends(get_db),
):
    result = build_impact_graph(
        db,
        event_id=event_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found.",
        )

    return result