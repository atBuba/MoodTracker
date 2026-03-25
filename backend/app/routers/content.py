import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.database import get_db
from app.models.employee import Employee
from app.models.motivation_content import MotivationContent
from app.middleware.auth import require_role
from app.utils.pagination import PaginationParams, paginate_response, success_response
from app.utils.exceptions import AppException
from app.schemas.content import ContentCreateRequest, ContentResponse

router = APIRouter(prefix="/api/content", tags=["Content"])

@router.get("")
async def list_content(
    type: str = Query(None, description="Filter by type: meme, quote, suggestion"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role(['manager', 'admin']))
):
    query = select(MotivationContent).order_by(desc(MotivationContent.created_at))
    
    if type:
        query = query.where(MotivationContent.type == type)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    result = await db.execute(query)
    contents = result.scalars().all()
    
    data = [ContentResponse.model_validate(c).model_dump() for c in contents]
    return paginate_response(data, total, pagination.page, pagination.per_page)

@router.post("")
async def create_content(
    payload: ContentCreateRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(require_role(['manager', 'admin']))
):
    new_content = MotivationContent(
        type=payload.type,
        content=payload.content,
        tags=payload.tags,
        created_by=current_user.id
    )
    db.add(new_content)
    await db.commit()
    return success_response({"message": "Content created successfully"})

@router.delete("/{id}")
async def delete_content(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(require_role(['manager', 'admin']))
):
    content = await db.get(MotivationContent, id)
    if not content:
        raise AppException(404, "NOT_FOUND", "Content not found")
        
    await db.delete(content)
    await db.commit()
    return success_response({"message": "Content deleted successfully"})