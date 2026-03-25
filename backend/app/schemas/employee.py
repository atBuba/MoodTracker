from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid
from datetime import date, datetime

class EmployeeUpdateSettings(BaseModel):
    analysis_allowed: bool

class EmployeeStateResponse(BaseModel):
    id: uuid.UUID
    date: date
    mood_index: float
    analysis_summary: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class ActivityResponse(BaseModel):
    id: uuid.UUID
    type: str
    source: str
    datetime: datetime
    model_config = ConfigDict(from_attributes=True)