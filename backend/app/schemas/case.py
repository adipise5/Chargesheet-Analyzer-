from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=120)
    police_station: str = Field(default="Not specified", max_length=160)
    language: str = Field(default="Gujarati / English", max_length=80)
    record_type: Literal["investigation", "educational_sample", "public_judgment"] = "investigation"


class CaseRecord(CaseCreate):
    id: str
    status: str
    is_demo: bool = False
    record_type: Literal["investigation", "educational_sample", "public_judgment"] = "investigation"
    created_at: datetime
    updated_at: datetime

