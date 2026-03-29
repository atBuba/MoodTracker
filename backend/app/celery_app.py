import os
from celery import Celery
from celery.schedules import crontab

# Configure broker (RabbitMQ) and backend (Redis) from environment variables
CELERY_BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "burnoutdetector",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.analysis", 
        "app.tasks.reports", 
        "app.tasks.motivation"
    ]
)

# Configuration for timezone and result expiration
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    result_expires=86400, # 1 day
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # 4.1. Trigger daily analysis at 18:00 every day
    "trigger-daily-analysis-at-18": {
        "task": "app.tasks.analysis.trigger_daily_analysis",
        "schedule": crontab(hour=18, minute=0),
    },
    # 4.2. Check and send manager reports every day at 09:00 AM
    # The task itself will decide if it's the right day for 'weekly' reports
    "trigger-manager-reports-at-09": {
        "task": "app.tasks.reports.trigger_manager_reports",
        "schedule": crontab(hour=9, minute=0),
    }
}