from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "collector",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "collect-mock-data": {
        "task": "app.tasks.mock_tasks.collect_mock",
        "schedule": crontab(minute=f"*/{settings.MOCK_INTERVAL_MINUTES}"),
    },
}

# Auto-discover tasks in app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])
