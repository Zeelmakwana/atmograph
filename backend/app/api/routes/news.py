"""
AtmoGraph News API.

Endpoints:

POST /news/analyze
    Manual article -> Event

POST /news/ingest-rss
    External RSS -> AtmoGraph Intelligence Pipeline

GET /news/monitor-status
    Live news monitor status
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.live_news_monitor import (
    live_news_monitor,
)
from app.services.news_ingestion_service import (
    NewsIngestionService,
)


def _resolve_user_id(current_user: User | None, db: Session) -> int | None:
    if current_user is not None and getattr(current_user, "id", None) is not None:
        return current_user.id
    from app.models.business_supply_chain import Company
    c = db.query(Company).order_by(Company.id.desc()).first()
    return c.user_id if c else None


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/news",
    tags=["News"],
)


# ============================================================
# MANUAL NEWS REQUEST
# ============================================================

class NewsAnalyzeRequest(BaseModel):
    """
    News article submitted manually.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    description: str = Field(
        default="",
        max_length=10000,
    )

    source: str | None = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# RSS INGESTION REQUEST
# ============================================================

class RSSIngestionRequest(BaseModel):
    """
    External RSS/Atom ingestion request.
    """

    feed_url: str | None = Field(
        default=None,
        description=(
            "RSS/Atom feed URL. "
            "If omitted, AtmoGraph uses its "
            "default supply-chain news feed."
        ),
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description=(
            "Maximum number of articles "
            "to inspect."
        ),
    )

    auto_simulate: bool = Field(
        default=True,
        description=(
            "Run the complete business "
            "supply-chain simulation."
        ),
    )


# ============================================================
# MANUAL NEWS ANALYSIS
# ============================================================

@router.post(
    "/analyze",
)
def analyze_news(
    request: NewsAnalyzeRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze manually supplied news
    and create an Event.
    """

    try:

        user_id = _resolve_user_id(current_user, db)
        service = NewsIngestionService(
            db,
            user_id=user_id,
        )

        result = service.process_news(
            title=request.title,
            description=request.description,
            source=request.source,
        )

        return {
            "success": True,
            "message": (
                "News analyzed and event "
                "created successfully."
            ),
            "data": result,
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
                "News ingestion failed: "
                f"{exc}"
            ),
        )


# ============================================================
# RSS INGESTION
# ============================================================

@router.post(
    "/ingest-rss",
)
def ingest_rss(
    request: RSSIngestionRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch external RSS/Atom news targeted to the active business
    and send relevant articles through the AtmoGraph Intelligence Pipeline.
    """

    try:

        user_id = _resolve_user_id(current_user, db)
        service = NewsIngestionService(
            db,
            user_id=user_id,
        )

        result = service.ingest_rss(
            feed_url=request.feed_url,
            limit=request.limit,
            auto_simulate=request.auto_simulate,
        )

        # Record scan metrics and audit history strictly for this user
        live_news_monitor.record_scan_result(result, user_id=user_id)

        return {
            "success": True,
            "message": (
                "RSS feed processed successfully."
            ),
            "data": result,
        }

    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:

        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "RSS ingestion failed: "
                f"{exc}"
            ),
        )


# ============================================================
# LIVE NEWS MONITOR STATUS & AUDIT TRAIL
# ============================================================

@router.get(
    "/monitor-status",
)
def monitor_status(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the current status, statistics, and audit trail of
    the background RSS news monitor strictly scoped to the active tenant.
    """
    user_id = _resolve_user_id(current_user, db)
    audit = live_news_monitor.get_audit_status(user_id=user_id, db=db)

    return {
        "success": True,
        "data": audit,
    }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "router",
    "NewsAnalyzeRequest",
    "RSSIngestionRequest",
]