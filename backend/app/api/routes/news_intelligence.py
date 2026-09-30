from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.services.intelligence_pipeline import (
    IntelligencePipeline,
)

from app.services.unified_intelligence_service import (
    UnifiedIntelligenceService,
)


router = APIRouter(
    prefix="/news-intelligence",
    tags=["News Intelligence"],
)


# ============================================================
# REQUEST
# ============================================================


class NewsIntelligenceRequest(
    BaseModel
):
    """
    Request for the complete AtmoGraph intelligence pipeline.
    """

    title: str = Field(
        ...,
        min_length=3,
        description="News or disruption title.",
    )

    description: str = Field(
        ...,
        min_length=5,
        description="Detailed disruption description.",
    )

    source: str = Field(
        default="manual",
        min_length=1,
        description="News source.",
    )

    auto_simulate: bool = Field(
        default=True,
        description=(
            "Run business supply-chain simulation "
            "after event analysis."
        ),
    )


# ============================================================
# ANALYZE
# ============================================================


@router.post(
    "/analyze",
)
def analyze_intelligence(
    payload: NewsIntelligenceRequest,
    db: Session = Depends(get_db),
):
    """
    Complete AtmoGraph intelligence pipeline.

    Flow:

        News
          ↓
        NLP
          ↓
        Event
          ↓
        Entity Resolution
          ↓
        Supply Chain
          ↓
        Business Simulation
          ↓
        Route Intelligence
          ↓
        Risk / Prediction
          ↓
        Unified Intelligence Contract

    The existing raw pipeline response is preserved for
    backward compatibility.

    A canonical `intelligence` object is added for frontend
    and downstream consumers.
    """

    try:

        pipeline = IntelligencePipeline(
            db
        )

        # ----------------------------------------------------
        # Support both newer and older pipeline signatures.
        # ----------------------------------------------------

        try:

            result = pipeline.process(
                title=payload.title,
                description=payload.description,
                source=payload.source,
                auto_simulate=payload.auto_simulate,
            )

        except TypeError as exc:

            if "auto_simulate" not in str(
                exc
            ):
                raise

            result = pipeline.process(
                title=payload.title,
                description=payload.description,
                source=payload.source,
            )

        # ----------------------------------------------------
        # Build canonical intelligence contract.
        # ----------------------------------------------------

        unified = (
            UnifiedIntelligenceService.build(
                result
            )
        )

        # ----------------------------------------------------
        # Preserve legacy response completely.
        #
        # DO NOT replace `result` with `unified`.
        # Existing frontend/tests may still consume:
        #
        # success
        # event_id
        # graph_id
        # message
        # event
        # nlp
        # business_supply_chain
        # prediction
        # ----------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            result["intelligence"] = (
                unified
            )

            result[
                "intelligence_version"
            ] = (
                UnifiedIntelligenceService.VERSION
            )

            return result

        # ----------------------------------------------------
        # Defensive fallback.
        # ----------------------------------------------------

        return {
            "success": True,
            "intelligence_version": (
                UnifiedIntelligenceService.VERSION
            ),
            "intelligence": unified,
            "raw": result,
        }

    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Intelligence pipeline failed: "
                f"{exc}"
            ),
        )


# ============================================================
# BACKWARD-COMPATIBILITY HELPER
# ============================================================


def _build_unified_intelligence(
    raw: dict,
) -> dict:
    """
    Backward-compatible unified response builder.

    Existing callers expect the original pipeline response
    fields such as:

        success
        event_id
        graph_id
        message
        event
        nlp
        business_supply_chain
        prediction

    Therefore the original response is preserved.

    The canonical intelligence contract is added under:

        result["intelligence"]

    Version is available under:

        result["intelligence_version"]
    """

    if not isinstance(
        raw,
        dict,
    ):
        raw = {}

    # --------------------------------------------------------
    # Preserve every original pipeline field.
    # --------------------------------------------------------

    result = dict(
        raw
    )

    # --------------------------------------------------------
    # Build canonical intelligence layer.
    # --------------------------------------------------------

    result["intelligence"] = (
        UnifiedIntelligenceService.build(
            raw
        )
    )

    result[
        "intelligence_version"
    ] = (
        UnifiedIntelligenceService.VERSION
    )

    return result


__all__ = [
    "router",
    "NewsIntelligenceRequest",
    "_build_unified_intelligence",
]