from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import date

class MoodTrendPoint(BaseModel):
    date: date
    mood_index: float

class RiskEmployeeResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    mood_index: float
    trend: Optional[str] = "stable"

class ManagerDashboardResponse(BaseModel):
    total_employees: int
    avg_mood_index: float
    at_risk_employees: List[RiskEmployeeResponse]
    mood_trend_30d: List[MoodTrendPoint]

class EmployeeDashboardResponse(BaseModel):
    mood_index: Optional[float]
    emotion: Optional[str]
    analysis_summary: Optional[str]
    mood_trend_30d: List[MoodTrendPoint]