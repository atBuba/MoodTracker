from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.employee import Employee
from app.models.manager_settings import ManagerSetting
from app.middleware.auth import require_role
from app.utils.pagination import success_response
from app.schemas.settings import ManagerSettingsUpdate, ManagerSettingsResponse

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db), current_user: Employee = Depends(require_role(['manager', 'admin']))):
    result = await db.execute(select(ManagerSetting).where(ManagerSetting.manager_id == current_user.id))
    setting = result.scalars().first()
    
    # Auto-create default settings if none exist
    if not setting:
        setting = ManagerSetting(manager_id=current_user.id)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

    return success_response(ManagerSettingsResponse.model_validate(setting).model_dump())

@router.patch("")
async def update_settings(
    payload: ManagerSettingsUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(require_role(['manager', 'admin']))
):
    result = await db.execute(select(ManagerSetting).where(ManagerSetting.manager_id == current_user.id))
    setting = result.scalars().first()
    
    if not setting:
        setting = ManagerSetting(manager_id=current_user.id)
        db.add(setting)

    if payload.threshold_value is not None:
        setting.threshold_value = payload.threshold_value
    if payload.notification_period is not None:
        setting.notification_period = payload.notification_period
    if payload.auto_motivation_enabled is not None:
        setting.auto_motivation_enabled = payload.auto_motivation_enabled

    await db.commit()
    return success_response({"message": "Settings updated successfully"})