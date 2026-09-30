"""
AtmoGraph NLP API Routes

Exposes the NLP engine through FastAPI.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.nlp_engine import nlp_engine


router = APIRouter(
    prefix="/nlp",
    tags=["NLP"],
)


class NLPAnalyzeRequest(BaseModel):
    """Input received from the client."""

    title: str = Field(..., min_length=1)
    description: str = Field(default="")


@router.get("/health")
def nlp_health():
    """
    Health check for the NLP engine.

    This endpoint verifies that the spaCy NLP engine
    is loaded and available.
    """

    model_loaded = bool(
        getattr(
            nlp_engine,
            "model_loaded",
            False,
        )
    )

    return {
        "success": True,
        "status": "online" if model_loaded else "offline",
        "model_loaded": model_loaded,
        "engine": "spaCy",
        "model": "en_core_web_sm",
    }


@router.post("/analyze")
def analyze_news(
    request: NLPAnalyzeRequest,
):
    """
    Analyze a news article and extract
    supply-chain intelligence.
    """

    result = nlp_engine.analyze(
        title=request.title,
        description=request.description,
    )

    return {
        "success": True,
        "data": result,
    }