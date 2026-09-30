from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    source: str
    event_type: str
    location: str | None = None
    severity: int = 1
    status: str = "active"


class EventResponse(BaseModel):
    id: int
    title: str
    description: str | None
    source: str | None
    event_type: str
    location: str | None
    severity: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)