from pydantic import BaseModel, Field

from .citation import Citation


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    aliases: list[str] = []
    confidence: float = Field(default=1.0, ge=0, le=1)
    metadata: dict = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    citations: list[Citation] = []
    extraction_method: str = "deterministic"
    human_verified: bool = False


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

