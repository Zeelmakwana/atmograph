from pydantic import BaseModel


class RiskResponse(BaseModel):
    event_id: int
    title: str
    risk_score: float
    risk_level: str
    event_type_score: int
    severity_score: int
    status_multiplier: float
    explanation: str