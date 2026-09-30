from pydantic import BaseModel, Field


class PredictedImpact(BaseModel):
    entity_type: str
    entity_name: str
    impact_type: str
    severity: str
    probability: float = Field(ge=0.0, le=1.0)
    estimated_delay_days: int = Field(ge=0)


class PredictionResponse(BaseModel):
    event_id: int
    event_title: str

    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: str

    primary_impact: str

    affected_regions: list[str]
    affected_products: list[str]
    affected_suppliers: list[str]

    impacts: list[PredictedImpact]

    explanation: list[str]