from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.event import Event


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


def serialize_event(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "event_id": event.id,
        "title": event.title,
        "name": event.title,
        "description": event.description,
        "source": event.source,
        "event_type": event.event_type,
        "type": event.event_type,
        "location": event.location,
        "severity": event.severity,
        "status": event.status,
        "company_id": getattr(event, "company_id", None),
        "event_time": (
            event.event_time.isoformat()
            if event.event_time
            else None
        ),
        "created_at": (
            event.created_at.isoformat()
            if event.created_at
            else None
        ),
        "updated_at": (
            event.updated_at.isoformat()
            if event.updated_at
            else None
        ),
    }


@router.get("")
def list_events(
    company_id: str = Query(
        default="",
        description="Filter by company or workspace ID",
    ),
    search: str = Query(
        default="",
        description="Search event title, description or source",
    ),
    severity: str = Query(
        default="",
        description="Filter by severity",
    ),
    status: str = Query(
        default="",
        description="Filter by event status",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    # Multi-business scoping: isolate events by active company
    if company_id.strip():
        cid = company_id.strip()
        if cid in ("C001", "adilqadri"):
            query = query.filter(Event.company_id.in_(["C001", "adilqadri"]))
        elif cid in ("mohilya", "C002"):
            query = query.filter(Event.company_id.in_(["mohilya", "C002"]))
        else:
            query = query.filter(Event.company_id == cid)
    else:
        from app.models.business_supply_chain import Company
        active_co = db.query(Company).first()
        if active_co:
            cname = (active_co.company_name or "").lower()
            if "adil" in cname or active_co.company_id == "C001":
                query = query.filter(Event.company_id.in_(["C001", "adilqadri"]))
            elif "mohilya" in cname:
                query = query.filter(Event.company_id.in_(["mohilya", "C002"]))
            elif active_co.company_id:
                query = query.filter(Event.company_id == active_co.company_id)

    if search.strip():
        term = f"%{search.strip()}%"

        query = query.filter(
            (
                Event.title.ilike(term)
            )
            | (
                Event.description.ilike(term)
            )
            | (
                Event.source.ilike(term)
            )
        )

    if severity.strip():
        query = query.filter(
            Event.severity.ilike(
                severity.strip()
            )
        )

    if status.strip():
        query = query.filter(
            Event.status.ilike(
                status.strip()
            )
        )

    events = (
        query
        .order_by(
            Event.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    items = [
        serialize_event(event)
        for event in events
    ]

    return {
        "success": True,
        "count": len(items),
        "events": items,
        "data": items,
    }


@router.get("/{event_id}")
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found",
        )

    return {
        "success": True,
        "data": serialize_event(event),
        "event": serialize_event(event),
    }