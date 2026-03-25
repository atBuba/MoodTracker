import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.database import get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.middleware.auth import get_current_user
from app.utils.pagination import PaginationParams, paginate_response, success_response
from app.utils.exceptions import AppException
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("")
async def list_notifications(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(get_current_user)
):
    query = select(Notification).where(Notification.manager_id == current_user.id).order_by(desc(Notification.created_at))
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    result = await db.execute(query)
    notifs = result.scalars().all()
    
    data = [NotificationResponse.model_validate(n).model_dump() for n in notifs]
    return paginate_response(data, total, pagination.page, pagination.per_page)

@router.patch("/{id}/read")
async def mark_as_read(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user)):
    notif = await db.get(Notification, id)
    
    if not notif or notif.manager_id != current_user.id:
        raise AppException(404, "NOT_FOUND", "Notification not found")
        
    notif.is_read = True
    await db.commit()
    return success_response({"message": "Marked as read"})

@router.get("/unread-count")
async def get_unread_count(db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user)):
    count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.manager_id == current_user.id, Notification.is_read == False)
    )
    return success_response({"unread_count": count or 0})