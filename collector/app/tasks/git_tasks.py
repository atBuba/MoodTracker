import asyncio
import logging

from app.celery_app import celery_app
from app.collectors.git import GitCollector

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.git_tasks.collect_git",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def collect_git(self) -> dict:
    """Celery task: collect commits and PR comments from GitHub repos."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_collect_git_async())
        finally:
            loop.close()
        return result
    except Exception as exc:
        logger.exception("Git collection task failed")
        raise self.retry(exc=exc)


async def _collect_git_async() -> dict:
    collector = GitCollector()
    try:
        from datetime import datetime, timezone

        activities = await collector.collect(since=datetime.now(timezone.utc))
        sent = await collector.send_to_backend(activities)
        return {"collected": len(activities), "sent": sent}
    finally:
        await collector.close()
