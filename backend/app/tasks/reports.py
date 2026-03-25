import asyncio
import logging
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy.future import select

from app.database import async_session_maker
from app.models.employee import Employee
from app.models.employee_state import EmployeeState
from app.models.manager_settings import ManagerSetting, NotificationPeriodEnum
from app.models.notification import Notification, NotificationTypeEnum
from app.services.email_service import send_email_sync

logger = logging.getLogger(__name__)

async def process_manager_reports_async(manager_id: str):
    async with async_session_maker() as session:
        # Fetch manager and settings
        manager = await session.get(Employee, manager_id)
        set_result = await session.execute(select(ManagerSetting).where(ManagerSetting.manager_id == manager_id))
        setting = set_result.scalars().first()
        
        if not manager or not setting:
            return

        threshold = setting.threshold_value
        period = setting.notification_period.value
        
        # Determine date range based on period
        days_back = 7 if period == 'weekly' else 1
        start_date = datetime.utcnow().date() - timedelta(days=days_back)

        # 1. Gather employees with mood_index < threshold
        # Join Employee and EmployeeState to get team members' states
        risk_result = await session.execute(
            select(Employee, EmployeeState)
            .join(EmployeeState, Employee.id == EmployeeState.employee_id)
            .where(
                Employee.team_id == manager.team_id,
                EmployeeState.date >= start_date,
                EmployeeState.mood_index < threshold
            )
        )
        
        risk_records = risk_result.all()
        if not risk_records:
            return # No report needed if everyone is fine

        # 2. Format HTML Report
        period_map = {"weekly": "еженедельный", "daily": "ежедневный"}
        ru_period = period_map.get(period, period)

        html_content = f"<h2>Отчет о настроении команды ({ru_period})</h2>"
        html_content += f"<p>Следующие сотрудники упали ниже порогового значения настроения ({threshold}):</p><ul>"
        
        for emp, state in risk_records:
            html_content += f"<li><b>{emp.full_name}</b>: Индекс настроения {state.mood_index} от {state.date}</li>"
        html_content += "</ul>"

        # 3. Save notification in DB
        notif = Notification(
            manager_id=manager.id,
            employee_id=manager.id, 
            type=NotificationTypeEnum.report,
            title=f"Отчет о настроении команды ({ru_period.capitalize()})",
            content=f"Сформирован отчет: выявлено {len(risk_records)} случаев риска."
        )
        session.add(notif)
        await session.commit()

        subject = f"Отчет о настроении команды — {datetime.now().strftime('%Y-%m-%d')}"
        
        return manager.email, subject, html_content
@shared_task(bind=True, max_retries=3)
def send_manager_report(self, manager_id: str):
    """
    Generates and sends report to a specific manager.
    Retries up to 3 times with exponential backoff on failure.
    """
    try:
        # Get data from DB
        report_data = asyncio.run(process_manager_reports_async(manager_id))
        
        if report_data:
            email, subject, html_content = report_data
            # Send email and handle errors via retry
            send_email_sync(to_email=email, subject=subject, content=html_content, is_html=True)
            logger.info(f"Report sent successfully to manager {manager_id}")
            
    except Exception as exc:
        logger.error(f"Failed to send report to {manager_id}. Retrying...")
        # Exponential backoff: 2s, 4s, 8s...
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task
def trigger_manager_reports():
    """
    Entry point to trigger reports for all managers based on their schedule.
    """
    async def get_managers_to_report():
        async with async_session_maker() as session:
            # Simple logic: If daily, send every day. If weekly, send only on Monday (weekday == 0)
            today_is_monday = datetime.utcnow().weekday() == 0
            
            query = select(ManagerSetting)
            if not today_is_monday:
                query = query.where(ManagerSetting.notification_period == NotificationPeriodEnum.daily)
                
            result = await session.execute(query)
            return [str(s.manager_id) for s in result.scalars().all()]

    manager_ids = asyncio.run(get_managers_to_report())
    for mid in manager_ids:
        # Dispatch sub-task for each manager
        send_manager_report.delay(mid)