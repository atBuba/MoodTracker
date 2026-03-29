import logging

from fastapi import FastAPI

from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="MoodTracker Data Collector (Mock Mode)",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "collector", "mode": "mock"}


@app.get("/health/detailed")
async def health_detailed() -> dict:
    return {
        "service": "collector",
        "status": "ok",
        "mode": "mock",
        "mock_interval_minutes": settings.MOCK_INTERVAL_MINUTES,
        "backend_url": settings.BACKEND_URL,
    }


@app.post("/generate-mock")
async def generate_mock() -> dict:
    """Manually trigger mock data generation (for testing)."""
    from datetime import datetime, timezone

    from app.collectors.mock import MockCollector

    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))
    sent = await collector.send_to_backend(activities)

    return {
        "generated": len(activities),
        "sent_to_backend": sent,
    }
