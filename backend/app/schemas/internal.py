from pydantic import BaseModel
from typing import Optional, Any
import uuid
from datetime import datetime, date

class ActivityCreateInternal(BaseModel):
    employee_email: str
    type: str
    source: str
    datetime: datetime
    data: dict 

class EmployeeStateInternal(BaseModel):
    employee_id: uuid.UUID
    date: date
    mood_index: float
    analysis_summary: str
    sentiment_data: Optional[dict] = None

class SentimentInternal(BaseModel):
    positive_ratio: float
    neutral_ratio: float
    negative_ratio: float
    emotion: str