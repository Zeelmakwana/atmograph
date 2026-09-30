from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.event_analytics import get_event_analytics


router = APIRouter(
    prefix="/analytics",
    tags=["Event Analytics"],
)


@router.get("/events")
def event_analytics(
    db: Session = Depends(get_db),
):
    return get_event_analytics(db)


@router.get("/events/{event_id}")
def event_analytics_by_id(
    event_id: int,
    db: Session = Depends(get_db),
):
    result = get_event_analytics(
        db,
        event_id=event_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found.",
        )

    return result