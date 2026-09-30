from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Event
from app.schemas.risk import RiskResponse
from app.services.risk_engine import calculate_risk


router = APIRouter(
    prefix="/risk",
    tags=["Risk Analysis"],
)


@router.get(
    "/event/{event_id}",
    response_model=RiskResponse,
)
def get_event_risk(
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
            detail="Event not found.",
        )

    result = calculate_risk(
        event_type=event.event_type,
        severity=event.severity,
        status=event.status,
    )

    explanation = (
        f"The event '{event.title}' has a "
        f"{result['risk_level']} risk level with a "
        f"risk score of {result['risk_score']}/100. "
        f"The score is based on event type, severity, "
        f"and current event status."
    )

    return RiskResponse(
        event_id=event.id,
        title=event.title,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        event_type_score=result["event_type_score"],
        severity_score=result["severity_score"],
        status_multiplier=result["status_multiplier"],
        explanation=explanation,
    )