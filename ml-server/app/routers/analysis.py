import logging

from fastapi import APIRouter, Depends, HTTPException, Header

from app.config import settings
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.schemas.productivity import ProductivityRequest, ProductivityResponse
from app.schemas.sentiment import SentimentRequest, SentimentResponse
from app.services.mood_service import analyze_mood
from app.services.productivity_service import analyze_productivity
from app.services.sentiment_service import analyze_sentiment

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ml", tags=["analysis"])


def _verify_api_key(x_internal_api_key: str = Header(...)) -> str:
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_internal_api_key


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    _key: str = Depends(_verify_api_key),
):
    """Comprehensive mood analysis. Returns mood_index and summary."""
    logger.info("POST /api/ml/analyze employee_id=%s activities=%d", request.employee_id, len(request.activities))
    try:
        result = await analyze_mood(
            employee_id=request.employee_id,
            activities=[a.model_dump() for a in request.activities],
        )
        return AnalyzeResponse(data=result)
    except Exception as exc:
        logger.exception("Mood analysis failed")
        raise HTTPException(
            status_code=503,
            detail="Analysis service temporarily unavailable",
            headers={"Retry-After": "30"},
        ) from exc


@router.post("/analyze-sentiment", response_model=SentimentResponse)
async def analyze_sentiment_endpoint(
    request: SentimentRequest,
    _key: str = Depends(_verify_api_key),
):
    """Batch text sentiment analysis."""
    logger.info("POST /api/ml/analyze-sentiment texts=%d", len(request.texts))
    try:
        results = await analyze_sentiment(request.texts)
        return SentimentResponse(data=results)
    except Exception as exc:
        logger.exception("Sentiment analysis failed")
        raise HTTPException(
            status_code=503,
            detail="Sentiment service temporarily unavailable",
            headers={"Retry-After": "30"},
        ) from exc


@router.post("/analyze-productivity", response_model=ProductivityResponse)
async def analyze_productivity_endpoint(
    request: ProductivityRequest,
    _key: str = Depends(_verify_api_key),
):
    """Productivity analysis from activity data."""
    logger.info("POST /api/ml/analyze-productivity employee_id=%s", request.employee_id)
    try:
        result = await analyze_productivity(
            employee_id=request.employee_id,
            activities=request.activities,
        )
        return ProductivityResponse(data=result)
    except Exception as exc:
        logger.exception("Productivity analysis failed")
        raise HTTPException(
            status_code=503,
            detail="Productivity service temporarily unavailable",
            headers={"Retry-After": "30"},
        ) from exc
