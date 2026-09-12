from pydantic import BaseModel, Field

from .citation import Citation


class QueryRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    graph_paths: list[list[str]] = []
    confidence: float = Field(ge=0, le=1)
    review_required: bool = False
    retrieval: list[dict] = []

