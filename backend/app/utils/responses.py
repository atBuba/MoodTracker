from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class Meta(BaseModel):
    total: int
    page: int
    per_page: int

class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[Meta] = None
    
def success_response(data: Any, meta: Optional[dict] = None) -> SuccessResponse:
    meta_obj = Meta(**meta) if meta else None
    return SuccessResponse(data=data, meta=meta_obj)

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail