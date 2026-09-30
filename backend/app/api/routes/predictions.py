from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Event
from app.schemas.prediction import PredictionResponse
from app.services.supply_chain_engine import (
    get_event_supply_chain_impact,
)

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


def _build_prediction_response(
    result,
) -> PredictionResponse:
    """
    Convert internal supply-chain engine result
    into the public API response schema.
    """

    return PredictionResponse(
        event_id=result.event_id,
        event_title=result.event_title,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        primary_impact=result.primary_impact,
        affected_regions=result.affected_regions,
        affected_products=result.affected_products,
        affected_suppliers=result.affected_suppliers,
        impacts=result.impacts,
        explanation=result.explanation,
    )


@router.get(
    "/event/{event_id}",
    response_model=PredictionResponse,
)
def predict_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate supply-chain impact prediction
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

    result = get_event_supply_chain_impact(
        db,
        event,
    )

    return _build_prediction_response(
        result
    )


@router.get("/")
def predict_all_events(
    db: Session = Depends(get_db),
):
    """
    Generate predictions for all stored events.
    """

    events = (
        db.query(Event)
        .order_by(Event.id.desc())
        .all()
    )

    predictions = []

    for event in events:

        result = get_event_supply_chain_impact(
            db,
            event,
        )

        predictions.append(
            _build_prediction_response(
                result
            )
        )

    return {
        "total_events": len(events),
        "predictions": predictions,
    }