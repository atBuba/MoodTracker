import os
import asyncio
import httpx
import logging
from datetime import datetime, timedelta, date
from celery import shared_task
from sqlalchemy.future import select

from app.database import async_session_maker
from app.models.employee import Employee
from app.models.activity import ActivityUnit
from app.models.employee_state import EmployeeState
from app.models.manager_settings import ManagerSetting
from app.models.notification import Notification, NotificationTypeEnum
from app.tasks.motivation import send_motivation

logger = logging.getLogger(__name__)

ML_SERVER_URL = os.getenv("ML_SERVER_URL", "http://ml-server:8001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "your-internal-api-key")

async def process_daily_analysis_async():
    async with async_session_maker() as session:
        # 1. Get all employees with analysis_allowed=True
        result = await session.execute(select(Employee).where(Employee.analysis_allowed == True))
        employees = result.scalars().all()

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        today = date.today()

        async with httpx.AsyncClient() as client:
            for emp in employees:
                try:
                    # Fetch last 30 days activity
                    act_result = await session.execute(
                        select(ActivityUnit)
                        .where(ActivityUnit.employee_id == emp.id, ActivityUnit.datetime >= thirty_days_ago)
                    )
                    activities = act_result.scalars().all()
                    
                    # Convert activities to dict for ML Server
                    activity_data = [
                        {"id": str(a.id), "type": a.type.value, "source": a.source, "datetime": a.datetime.isoformat()} 
                        for a in activities
                    ]

                    # 2. Send request to ML Server
                    ml_response = await client.post(
                        f"{ML_SERVER_URL}/api/ml/analyze",
                        headers={"X-Internal-Api-Key": INTERNAL_API_KEY},
                        json={"employee_id": str(emp.id), "activities": activity_data},
                        timeout=30.0
                    )
                    ml_response.raise_for_status()
                    ml_data = ml_response.json().get("data", {})

                    # Extract data from ML response
                    mood_index = ml_data.get("mood_index", 0.5)
                    analysis_summary = ml_data.get("summary", "No summary provided.")
                    
                    # 3. Save to employee_states
                    new_state = EmployeeState(
                        employee_id=emp.id,
                        mood_index=mood_index,
                        date=today,
                        analysis_summary=analysis_summary
                    )
                    session.add(new_state)

                    # 4. Check manager thresholds and auto-motivation
                    if emp.team_id:
                        # Find manager of this team
                        mgr_result = await session.execute(
                            select(Employee).where(Employee.team_id == emp.team_id, Employee.role == 'manager')
                        )
                        manager = mgr_result.scalars().first()

                        if manager:
                            # Get manager settings
                            set_result = await session.execute(select(ManagerSetting).where(ManagerSetting.manager_id == manager.id))
                            setting = set_result.scalars().first()
                            
                            threshold = setting.threshold_value if setting else 0.4
                            auto_motivation = setting.auto_motivation_enabled if setting else True

                            if mood_index < threshold:
                                # Create alert notification for manager
                                alert = Notification(
                                    manager_id=manager.id,
                                    employee_id=emp.id,
                                    type=NotificationTypeEnum.alert,
                                    title="Low Mood Alert",
                                    content=f"Employee {emp.full_name}'s mood index dropped to {mood_index}."
                                )
                                session.add(alert)

                                # 5. Trigger auto motivation if enabled
                                if auto_motivation:
                                    # Call the motivation celery task asynchronously
                                    send_motivation.delay(str(emp.id), str(manager.id))

                except Exception as e:
                    logger.error(f"Error processing analysis for employee {emp.id}: {str(e)}")
                    continue # Continue with next employee even if one fails

        await session.commit()

@shared_task
def trigger_daily_analysis():
    logger.info("Starting daily analysis task...")
    asyncio.run(process_daily_analysis_async())
    logger.info("Daily analysis task completed.")