from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Trend(str, Enum):
    STABLE = "stable"
    IMPROVING = "improving"
    DECLINING = "declining"


class ActivityItem(BaseModel):
    id: str
    type: str
    source: str
    datetime: str
    metadata: Optional[dict] = None


class ProductivityRequest(BaseModel):
    employee_id: str
    activities: list[ActivityItem]


class ProductivityResult(BaseModel):
    productivity_score: float = Field(ge=0.0, le=1.0)
    patterns: list[str]
    trend: Trend


class ProductivityResponse(BaseModel):
    data: ProductivityResult
