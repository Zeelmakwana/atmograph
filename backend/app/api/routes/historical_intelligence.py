from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.core.database import get_db
from app.models.business_supply_chain import BusinessSupplier, Company
from app.models.user import User
from app.services.historical_intelligence_service import (
    HistoricalIntelligenceService,
)


router = APIRouter(
    prefix="/historical-intelligence",
    tags=["Historical Intelligence"],
)


def _resolve_user_context(
    current_user: User | None,
    company_id: str,
    db: Session,
) -> tuple[int | None, str, int]:
    """
    Resolve active user, tenant company ID, and supplier count.
    """
    user_id = None
    if current_user is not None and getattr(current_user, "id", None) is not None:
        user_id = current_user.id

    if user_id is None:
        latest_co = db.query(Company).order_by(Company.id.desc()).first()
        if latest_co and latest_co.user_id:
            user_id = latest_co.user_id

    company = None
    if user_id is not None:
        company = db.query(Company).filter(Company.user_id == user_id).first()

    if not company and company_id:
        company = db.query(Company).filter(Company.company_id == company_id.strip()).first()

    suppliers_count = 0
    if user_id is not None:
        suppliers_count = (
            db.query(BusinessSupplier)
            .filter(BusinessSupplier.user_id == user_id)
            .count()
        )

    resolved_cid = company.company_id if company else company_id.strip()
    return user_id, resolved_cid, suppliers_count


@router.get("/history")
def history(
    company_id: str = "",
    search: str = "",
    severity: str = "",
    status: str = "",
    event_type: str = "",
    source: str = "",
    limit: int = Query(100, ge=1, le=500),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    limit_val = int(getattr(limit, "default", limit))
    user_id, target_cid, suppliers_count = _resolve_user_context(
        current_user, company_id, db
    )

    # A fresh business account with NO suppliers registered yet has 0 historical events!
    if suppliers_count == 0:
        return {
            "success": True,
            "version": "1.0",
            "count": 0,
            "events": [],
            "clusters": [],
        }

    return HistoricalIntelligenceService(db).list_history(
        company_id=target_cid,
        search=search,
        severity=severity,
        status=status,
        event_type=event_type,
        source=source,
        limit=limit_val,
    )


@router.get("/clusters")
def clusters(
    company_id: str = "",
    limit: int = Query(100, ge=1, le=500),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    limit_val = int(getattr(limit, "default", limit))
    user_id, target_cid, suppliers_count = _resolve_user_context(
        current_user, company_id, db
    )

    if suppliers_count == 0:
        return {
            "success": True,
            "version": "1.0",
            "count": 0,
            "clusters": [],
        }

    return HistoricalIntelligenceService(db).clusters(
        company_id=target_cid,
        limit=limit_val,
    )


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

