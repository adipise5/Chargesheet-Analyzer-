from datetime import datetime
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=120)
    police_station: str = Field(default="Not specified", max_length=160)
    language: str = Field(default="Gujarati / English", max_length=80)


class CaseRecord(CaseCreate):
    id: str
    status: str
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime

