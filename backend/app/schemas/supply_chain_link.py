from pydantic import BaseModel


class SupplyChainLinkCreate(BaseModel):
    event_id: int
    supplier_id: int
    product_id: int

    relationship_type: str = "affected"
    impact_level: str = "medium"
    estimated_delay_days: int = 0


class SupplyChainLinkResponse(SupplyChainLinkCreate):
    id: int

    class Config:
        from_attributes = True