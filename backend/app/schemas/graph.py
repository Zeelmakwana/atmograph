from pydantic import BaseModel


class GraphStatusResponse(BaseModel):
    status: str
    service: str