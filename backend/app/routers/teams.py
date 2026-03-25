import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.models.team import Team
from app.models.employee import Employee
from app.models.employee_state import EmployeeState
from app.middleware.auth import get_current_user
from app.utils.pagination import success_response
from app.utils.exceptions import AppException
from app.schemas.team import TeamResponse, TeamDetailResponse
from app.schemas.auth import UserResponse
from app.utils.pagination import PaginationParams 

router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.get("")
async def list_teams(
    params: PaginationParams = Depends(), 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(get_current_user)
):
    result = await db.execute(
        select(Team).offset(params.skip).limit(params.limit)
    )
    teams = result.scalars().all()

    count_result = await db.execute(select(func.count(Team.id)))
    total_count = count_result.scalar()

    return success_response(
        data=[TeamResponse.model_validate(t).model_dump() for t in teams],
        meta={
            "total": total_count,
            "page": params.page,
            "per_page": params.per_page
        }
    )

@router.get("/{id}")
async def get_team_detail(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(get_current_user)
):
    team = await db.get(Team, id)
    
    if not team:
        raise AppException(
            status_code=404, 
            code="TEAM_NOT_FOUND", 
            message="Team not found"
        )

    # Average mood_index
    mood_query = (
        select(func.avg(EmployeeState.mood_index))
        .join(Employee, Employee.id == EmployeeState.employee_id)
        .where(Employee.team_id == id)
    )
    
    mood_result = await db.execute(mood_query)
    avg_mood = mood_result.scalar() or 0  

    return success_response({
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "average_mood": round(float(avg_mood), 2), 
        "created_at": team.created_at
    })

@router.get("/{id}/employees")
async def get_team_employees(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user)):
    # Logic DB query employees where team_id = id
    result = await db.execute(select(Employee).where(Employee.team_id == id))
    employees = result.scalars().all()
    return success_response([UserResponse.model_validate(e).model_dump() for e in employees])