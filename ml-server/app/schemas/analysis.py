from typing import Optional

from pydantic import BaseModel, Field


class ActivityItem(BaseModel):
    id: str
    type: str
    source: str
    datetime: str
    metadata: Optional[dict] = None


class AnalyzeRequest(BaseModel):
    employee_id: str
    activities: list[ActivityItem]


class AnalyzeData(BaseModel):
    mood_index: float = Field(ge=0.0, le=1.0)
    summary: str


class AnalyzeResponse(BaseModel):
    data: AnalyzeData
