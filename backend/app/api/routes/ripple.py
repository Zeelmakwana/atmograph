from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Event
from app.services.ripple_engine import build_ripple_graph


router = APIRouter(
    prefix="/ripple",
    tags=["Ripple Effect"],
)


@router.get("/event/{event_id}")
def get_event_ripple(
    event_id: int,
    db: Session = Depends(get_db),
):
    """
    Build the complete ripple-effect graph
    for a specific supply-chain event.
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

    return build_ripple_graph(db, event_id)
