from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Event
from app.schemas.analysis import AnalysisSummary
from app.services.analysis_engine import analyze_event


router = APIRouter(
    prefix="/analysis",
    tags=["Event Analysis"],
)


@router.get(
    "/event/{event_id}",
    response_model=AnalysisSummary,
)
def get_event_analysis(
    event_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a unified supply-chain analysis
    for a specific event.
    """

    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found.",
        )

    return analyze_event(
        event=event,
        db=db,
    )