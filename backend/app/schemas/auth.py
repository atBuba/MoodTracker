from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
import uuid

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    team_id: Optional[uuid.UUID]
    analysis_allowed: bool
    
    model_config = ConfigDict(from_attributes=True)