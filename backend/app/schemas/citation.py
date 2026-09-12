from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    page: int = Field(ge=1)
    chunk_id: str
    label: str

