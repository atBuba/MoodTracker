from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime

class ContentCreateRequest(BaseModel):
    type: str # 'meme', 'quote', 'suggestion'
    content: str
    tags: Optional[List[str]] = []

class ContentResponse(BaseModel):
    id: uuid.UUID
    type: str
    content: str
    tags: List[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)