from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid

class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class TeamDetailResponse(TeamResponse):
    avg_mood_index: Optional[float] = None