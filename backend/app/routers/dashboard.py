from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, cast, Numeric
from datetime import datetime, timedelta

from app.database import get_db
from app.models.employee import Employee
from app.models.employee_state import EmployeeState
from app.models.manager_settings import ManagerSetting
from app.middleware.auth import get_current_user, require_role
from app.utils.pagination import success_response
from app.schemas.dashboard import ManagerDashboardResponse, EmployeeDashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/manager")
async def get_manager_dashboard(
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(require_role(['manager', 'admin']))
):
    setting_res = await db.execute(select(ManagerSetting).where(ManagerSetting.manager_id == current_user.id))
    setting = setting_res.scalars().first()
    threshold = setting.threshold_value if setting else 0.4

    # Task employees in the same team
    emp_res = await db.execute(select(Employee).where(Employee.team_id == current_user.team_id))
    employees = emp_res.scalars().all()
    emp_ids = [e.id for e in employees]

    if not emp_ids:
        return success_response({"total_employees": 0, "avg_mood_index": 0.0, "at_risk_employees": [], "mood_trend_30d": []})

    # Take latest mood index for each employee and calculate risk
    risk_employees = []
    total_mood = 0.0
    valid_mood_count = 0

    for emp in employees:
        state_res = await db.execute(
            select(EmployeeState)
            .where(EmployeeState.employee_id == emp.id)
            .order_by(desc(EmployeeState.date))
            .limit(1)
        )
        latest_state = state_res.scalars().first()
        
        if latest_state:
            total_mood += latest_state.mood_index
            valid_mood_count += 1
            if latest_state.mood_index < threshold:
                risk_employees.append({
                    "id": emp.id,
                    "full_name": emp.full_name,
                    "mood_index": latest_state.mood_index,
                    "trend": "declining" 
                })

    avg_mood = total_mood / valid_mood_count if valid_mood_count > 0 else 0.0

    # Build 30-day mood trend (average across all team employees per day)
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    trend_res = await db.execute(
        select(
            EmployeeState.date,
            func.round(cast(func.avg(EmployeeState.mood_index), Numeric), 2).label("avg_mood"),
        )
        .where(
            EmployeeState.employee_id.in_(emp_ids),
            EmployeeState.date >= thirty_days_ago,
        )
        .group_by(EmployeeState.date)
        .order_by(EmployeeState.date)
    )
    mood_trend = [{"date": str(row.date), "mood_index": float(row.avg_mood)} for row in trend_res]

    return success_response({
        "total_employees": len(employees),
        "avg_mood_index": round(avg_mood, 2),
        "at_risk_employees": risk_employees,
        "mood_trend_30d": mood_trend,
    })

@router.get("/employee")
async def get_employee_dashboard(
    db: AsyncSession = Depends(get_db), 
    current_user: Employee = Depends(require_role(['employee']))
):
    # Take 30-days history for current employee
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    
    result = await db.execute(
        select(EmployeeState)
        .where(EmployeeState.employee_id == current_user.id, EmployeeState.date >= thirty_days_ago)
        .order_by(desc(EmployeeState.date))
    )
    states = result.scalars().all()
    
    if not states:
        return success_response({"mood_index": None, "emotion": None, "analysis_summary": None, "mood_trend_30d": []})

    latest = states[0]
    trend = [{"date": s.date, "mood_index": s.mood_index} for s in reversed(states)]

    return success_response({
        "mood_index": latest.mood_index,
        "emotion": "neutral", 
        "analysis_summary": latest.analysis_summary,
        "mood_trend_30d": trend
    })