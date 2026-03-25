from pydantic import BaseModel, ConfigDict
from typing import Optional

class ManagerSettingsUpdate(BaseModel):
    threshold_value: Optional[float] = None
    notification_period: Optional[str] = None
    auto_motivation_enabled: Optional[bool] = None

class ManagerSettingsResponse(BaseModel):
    threshold_value: float
    notification_period: str
    auto_motivation_enabled: bool
    
    model_config = ConfigDict(from_attributes=True)