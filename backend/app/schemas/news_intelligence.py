from __future__ import annotations

from pydantic import BaseModel, Field


class NewsAnalysisRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        description="News or disruption title",
    )

    description: str = Field(
        ...,
        min_length=5,
        description="Detailed news/disruption description",
    )

    source: str | None = Field(
        default="manual",
        description="News source",
    )

    auto_simulate: bool = Field(
        default=True,
        description=(
            "Automatically run business supply-chain "
            "impact simulation when a supplier is resolved."
        ),
    )