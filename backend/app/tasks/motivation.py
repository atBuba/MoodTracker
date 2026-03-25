import os
import asyncio
import httpx
import logging
from celery import shared_task
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from app.database import async_session_maker
from app.models.employee import Employee
from app.models.motivation_content import MotivationContent, MotivationTypeEnum
from app.models.notification import Notification, NotificationTypeEnum
from app.services.email_service import send_email_sync

logger = logging.getLogger(__name__)
ML_SERVER_URL = os.getenv("ML_SERVER_URL", "http://ml-server:8001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "your-internal-api-key")

async def process_motivation_async(employee_id: str, manager_id: str):
    async with async_session_maker() as session:
        emp = await session.get(Employee, employee_id)
        if not emp:
            raise ValueError(f"Employee {employee_id} not found")

        # 1. Pick random motivation content
        # Using order_by(func.random()) is specific to PostgreSQL/SQLite
        content_res = await session.execute(
            select(MotivationContent).order_by(func.random()).limit(1)
        )
        motivation = content_res.scalars().first()

        if not motivation:
            raise ValueError("No motivation content available in database")

        final_content_text = motivation.content
        subject = "A little motivation for you!"

        # 2. If type is meme, call ML Server to generate it
        if motivation.type == MotivationTypeEnum.meme:
            async with httpx.AsyncClient() as client:
                ml_response = await client.post(
                    f"{ML_SERVER_URL}/api/ml/generate-meme",
                    headers={"X-Internal-Api-Key": INTERNAL_API_KEY},
                    json={"context": motivation.content},
                    timeout=60.0 # Image generation might take longer
                )
                ml_response.raise_for_status()
                # Assuming ML server returns a URL to the generated image in MinIO
                image_url = ml_response.json().get("data", {}).get("image_url")
                
                if image_url:
                    # Construct HTML with image
                    final_content_text = f"<h3>Cheer up!</h3><br><img src='{image_url}' alt='Motivation Meme'>"
                    is_html = True
                else:
                    is_html = False # Fallback to text
        else:
            is_html = False

        # 4. Create notification for manager
        notif = Notification(
            manager_id=manager_id,
            employee_id=emp.id,
            type=NotificationTypeEnum.motivation_sent,
            title="Motivation Sent",
            content=f"Sent a {motivation.type.value} to {emp.full_name}."
        )
        session.add(notif)
        await session.commit()

        return emp.email, subject, final_content_text, is_html

@shared_task(bind=True, max_retries=3)
def send_motivation(self, employee_id: str, manager_id: str):
    """
    Sends motivation content. If fails (e.g., SMTP down, ML Server down), 
    retries in 30 minutes.
    """
    try:
        # Execute DB and API calls asynchronously
        emp_email, subject, content, is_html = asyncio.run(process_motivation_async(employee_id, manager_id))
        
        send_email_sync(to_email=emp_email, subject=subject, content=content, is_html=is_html)
        logger.info(f"Motivation sent successfully to {emp_email}")
        
    except Exception as exc:
        logger.error(f"Failed to send motivation to {employee_id}. Retrying in 30 mins... Error: {str(exc)}")
        # Retry in 30 minutes
        raise self.retry(exc=exc, countdown=1800)