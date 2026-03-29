import asyncio
import logging

from app.celery_app import celery_app
from app.collectors.calendar import CalendarCollector

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.calendar_tasks.collect_calendar",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def collect_calendar(self) -> dict:
    """Celery task: collect events from Google Calendar."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_collect_calendar_async())
        finally:
            loop.close()
        return result
    except Exception as exc:
        logger.exception("Calendar collection task failed")
        raise self.retry(exc=exc)


async def _collect_calendar_async() -> dict:
    collector = CalendarCollector()
    try:
        from datetime import datetime, timezone

        activities = await collector.collect(since=datetime.now(timezone.utc))
        sent = await collector.send_to_backend(activities)
        return {"collected": len(activities), "sent": sent}
    finally:
        await collector.close()
