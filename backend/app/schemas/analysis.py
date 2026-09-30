from pydantic import BaseModel, Field


class AnalysisSummary(BaseModel):
    event_id: int
    event_title: str

    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: str

    impact_score: float = Field(ge=0.0, le=100.0)
    impact_level: str

    estimated_delay_days: int = Field(ge=0)

    supplier_count: int = Field(ge=0)
    product_count: int = Field(ge=0)

    affected_regions: list[str]
    affected_suppliers: list[str]
    affected_products: list[str]

    explanation: list[str]