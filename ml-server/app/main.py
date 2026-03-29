import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import analysis, generation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_start_time: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    _start_time = datetime.now(timezone.utc)
    # Pre-load prompts
    for name in ("sentiment.txt", "productivity.txt", "mood_analysis.txt"):
        path = settings.prompts_dir / name
        if path.exists():
            logger.info("Loaded prompt: %s (%d bytes)", name, path.stat().st_size)
        else:
            logger.warning("Prompt file not found: %s", path)
    logger.info("ML Server started")
    yield
    logger.info("ML Server shutting down")


app = FastAPI(
    title="MoodTracker ML Server",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(analysis.router)
app.include_router(generation.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_detailed():
    openrouter_configured = bool(settings.openrouter_api_key)
    minio_configured = bool(settings.minio_url)

    return {
        "status": "ok",
        "uptime_since": _start_time.isoformat() if _start_time else None,
        "services": {
            "openrouter": "configured" if openrouter_configured else "not_configured",
            "llm_model": settings.openrouter_llm_model,
            "image_model": settings.openrouter_image_model,
            "minio": "configured" if minio_configured else "not_configured",
        },
    }
