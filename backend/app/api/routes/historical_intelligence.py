from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.historical_intelligence_service import (
    HistoricalIntelligenceService,
)


router = APIRouter(
    prefix="/historical-intelligence",
    tags=["Historical Intelligence"],
)


@router.get("/history")
def history(
    company_id: str = "",
    search: str = "",
    severity: str = "",
    status: str = "",
    event_type: str = "",
    source: str = "",
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return HistoricalIntelligenceService(db).list_history(
        company_id=company_id,
        search=search,
        severity=severity,
        status=status,
        event_type=event_type,
        source=source,
        limit=limit,
    )


@router.get("/clusters")
def clusters(
    company_id: str = "",
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return HistoricalIntelligenceService(db).clusters(limit=limit)


@router.get("/timeline/{event_id}")
def timeline(
    event_id: int,
    db: Session = Depends(get_db),
):
    result = HistoricalIntelligenceService(db).timeline(event_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get(
                "message",
                "Event not found.",
            ),
        )

    return result



@router.get("/intelligence/{event_id}")
def intelligence(
    event_id: int,
    db: Session = Depends(get_db),
):
    result = HistoricalIntelligenceService(
        db
    ).intelligence(event_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get(
                "message",
                "Event not found.",
            ),
        )

    return result

@router.get("/replay/{event_id}")
def replay(
    event_id: int,
    db: Session = Depends(get_db),
):
    result = HistoricalIntelligenceService(db).replay(event_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get(
                "message",
                "Event not found.",
            ),
        )

    return result

