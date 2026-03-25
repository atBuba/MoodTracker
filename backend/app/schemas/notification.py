from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    content: str
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)