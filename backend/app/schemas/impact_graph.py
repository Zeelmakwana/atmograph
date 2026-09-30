from pydantic import BaseModel


class ImpactGraphNode(BaseModel):
    id: str
    type: str
    label: str
    data: dict


class ImpactGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    label: str


class ImpactGraphResponse(BaseModel):
    event_id: int
    event_title: str

    nodes: list[ImpactGraphNode]
    edges: list[ImpactGraphEdge]

    total_nodes: int
    total_edges: int