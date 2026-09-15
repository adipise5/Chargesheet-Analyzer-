from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    id: str
    case_id: str
    filename: str
    category: str = "unknown"
    page_count: int = 0
    sha256: str
    status: str
    role: str = "supporting_record"


class PageRecord(BaseModel):
    id: str
    document_id: str
    page_number: int = Field(ge=1)
    extraction_method: str
    language: str
    original_text: str
    normalized_text: str
    ocr_confidence: float = Field(ge=0, le=100)
    review_status: str
    tesseract_text: str | None = None
    vision_candidate_text: str | None = None
    corrected_text: str | None = None

