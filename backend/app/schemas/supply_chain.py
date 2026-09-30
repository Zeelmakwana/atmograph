from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SupplyChainImportResult(BaseModel):
    """
    Result returned by the AtmoGraph supply-chain
    Excel validation and normalization pipeline.
    """

    success: bool

    filename: str

    sheets_found: list[str]

    sheets_validated: list[str]

    row_counts: dict[str, int]

    warnings: list[str] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    records: dict[
        str,
        list[dict[str, Any]]
    ] = Field(
        default_factory=dict
    )