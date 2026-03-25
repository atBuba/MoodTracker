import uuid
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.models.employee import Employee
from app.models.employee_state import EmployeeState
from app.models.activity import ActivityUnit
from app.middleware.auth import get_current_user, require_role
from app.utils.pagination import PaginationParams, paginate_response, success_response
from app.utils.exceptions import AppException
from app.schemas.employee import EmployeeUpdateSettings, EmployeeStateResponse, ActivityResponse
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/api/employees", tags=["Employees"])

async def verify_employee_access(id: uuid.UUID, current_user: Employee, db: AsyncSession) -> Employee:
    if current_user.role.value == 'employee' and current_user.id != id:
        raise AppException(403, "FORBIDDEN", "You can only view your own data")
        
    employee = await db.get(Employee, id)
    if not employee:
        raise AppException(404, "NOT_FOUND", "Employee not found")
        
    if current_user.role.value == 'manager' and employee.team_id != current_user.team_id:
        raise AppException(403, "FORBIDDEN", "Employee is not in your team")
        
    return employee


# API Endpoints

@router.get("")
async def list_employees(
    team_id: uuid.UUID = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role(['manager', 'admin']))
):
    query = select(Employee)
    
    if current_user.role.value == 'manager':
        query = query.where(Employee.team_id == current_user.team_id)
    elif team_id:
        query = query.where(Employee.team_id == team_id)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    data = [UserResponse.model_validate(e).model_dump() for e in employees]
    return paginate_response(data, total, pagination.page, pagination.per_page)

@router.get("/{id}")
async def get_employee(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(get_current_user)
):
    employee = await verify_employee_access(id, current_user, db)
    return success_response(UserResponse.model_validate(employee).model_dump())

@router.get("/{id}/states")
async def get_employee_states(
    id: uuid.UUID,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    await verify_employee_access(id, current_user, db)
    
    query = select(EmployeeState).where(EmployeeState.employee_id == id).order_by(EmployeeState.date.desc())
    if date_from:
        query = query.where(EmployeeState.date >= date_from)
    if date_to:
        query = query.where(EmployeeState.date <= date_to)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    result = await db.execute(query)
    states = result.scalars().all()
    
    data = [EmployeeStateResponse.model_validate(s).model_dump() for s in states]
    return paginate_response(data, total, pagination.page, pagination.per_page)

@router.get("/{id}/activity")
async def get_employee_activity(
    id: uuid.UUID,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    type: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    await verify_employee_access(id, current_user, db)
    
    query = select(ActivityUnit).where(ActivityUnit.employee_id == id).order_by(ActivityUnit.datetime.desc())
    if date_from:
        query = query.where(ActivityUnit.datetime >= date_from)
    if date_to:
        query = query.where(ActivityUnit.datetime <= date_to)
    if type:
        query = query.where(ActivityUnit.type == type)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    data = [ActivityResponse.model_validate(a).model_dump() for a in activities]
    return paginate_response(data, total, pagination.page, pagination.per_page)

@router.patch("/me/settings")
async def update_my_settings(
    payload: EmployeeUpdateSettings, 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(get_current_user)
):
    current_user.analysis_allowed = payload.analysis_allowed
    await db.commit()
    return success_response({"message": "Settings updated"})