from pydantic import BaseModel


class DashboardOverview(BaseModel):
    total_events: int
    active_events: int
    total_suppliers: int
    total_products: int
    total_relationships: int
    affected_suppliers: int
    affected_products: int
    estimated_total_delay_days: int


class RiskDistribution(BaseModel):
    high: int
    medium: int
    low: int
    unknown: int


class EventTypeCount(BaseModel):
    event_type: str
    count: int


class LocationCount(BaseModel):
    location: str
    count: int


class DashboardResponse(BaseModel):
    overview: DashboardOverview
    risk_distribution: RiskDistribution
    event_types: list[EventTypeCount]
    locations: list[LocationCount]