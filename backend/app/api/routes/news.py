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

from app.core.database import get_db
from app.services.live_news_monitor import (
    live_news_monitor,
)
from app.services.news_ingestion_service import (
    NewsIngestionService,
)


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
    db: Session = Depends(get_db),
):
    """
    Analyze manually supplied news
    and create an Event.
    """

    try:

        service = NewsIngestionService(
            db
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
    db: Session = Depends(get_db),
):
    """
    Fetch external RSS/Atom news and send
    new articles through the complete
    AtmoGraph Intelligence Pipeline.

    Flow:

        RSS
          ↓
        Article
          ↓
        NLP
          ↓
        Event
          ↓
        Supplier Matching
          ↓
        Business Simulation
          ↓
        Route Impact
          ↓
        Resilience
          ↓
        Risk
          ↓
        GNN / Hybrid
          ↓
        Unified Intelligence
    """

    try:

        service = NewsIngestionService(
            db
        )

        result = service.ingest_rss(
            feed_url=request.feed_url,
            limit=request.limit,
            auto_simulate=request.auto_simulate,
        )

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
# LIVE NEWS MONITOR STATUS
# ============================================================

@router.get(
    "/monitor-status",
)
def monitor_status():
    """
    Return the current status of the
    background RSS news monitor.
    """

    return {
        "success": True,
        "data": {
            "running": (
                live_news_monitor.running
            ),
            "interval_seconds": (
                live_news_monitor.interval_seconds
            ),
            "limit": (
                live_news_monitor.limit
            ),
            "auto_simulate": (
                live_news_monitor.auto_simulate
            ),
        },
    }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "router",
    "NewsAnalyzeRequest",
    "RSSIngestionRequest",
]