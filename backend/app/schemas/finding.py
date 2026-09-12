from enum import StrEnum
from pydantic import BaseModel, Field, model_validator

from .citation import Citation


class Classification(StrEnum):
    STRONGLY_CORROBORATED = "STRONGLY_CORROBORATED"
    MODERATELY_CORROBORATED = "MODERATELY_CORROBORATED"
    LIMITED_CORROBORATION = "LIMITED_CORROBORATION"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class Finding(BaseModel):
    id: str
    type: str
    title: str
    summary: str
    classification: Classification
    confidence: float = Field(ge=0, le=1)
    supporting_sources: list[Citation] = []
    contradicting_sources: list[Citation] = []
    entities: list[str] = []
    factors: dict[str, float | int | bool] = {}
    human_review_required: bool = False
    verified: bool = False
    issue: str = ""
    differences: list[dict[str, str]] = []
    why_important: str = ""
    recommended_correction: str = ""
    io_action: str = ""
    defense_questions: list[str] = []
    related_document_roles: list[str] = []

    @model_validator(mode="after")
    def confirmed_findings_require_sources(self):
        if self.verified and not (self.supporting_sources or self.contradicting_sources):
            raise ValueError("A verified finding must contain provenance")
        return self

