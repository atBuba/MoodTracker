import asyncio
import logging

from app.celery_app import celery_app
from app.collectors.mock import MockCollector

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.mock_tasks.collect_mock",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def collect_mock(self) -> dict:
    """Celery task: generate mock data and send to backend."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_collect_mock_async())
        finally:
            loop.close()
        return result
    except Exception as exc:
        logger.exception("Mock collection task failed")
        raise self.retry(exc=exc)


async def _collect_mock_async() -> dict:
    from datetime import datetime, timezone

    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))
    sent = await collector.send_to_backend(activities)
    return {"collected": len(activities), "sent": sent}
