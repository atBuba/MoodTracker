import logging

from fastapi import APIRouter, Depends, HTTPException, Header

from app.config import settings
from app.schemas.meme import MemeRequest, MemeResponse, MemeData
from app.services.meme_service import generate_meme

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ml", tags=["generation"])


def _verify_api_key(x_internal_api_key: str = Header(...)) -> str:
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_internal_api_key


@router.post("/generate-meme", response_model=MemeResponse)
async def generate_meme_endpoint(
    request: MemeRequest,
    _key: str = Depends(_verify_api_key),
):
    """Generate a meme based on context."""
    logger.info("POST /api/ml/generate-meme context_len=%d", len(request.context))
    try:
        image_url = await generate_meme(request.context)
        return MemeResponse(data=MemeData(image_url=image_url))
    except Exception as exc:
        logger.exception("Meme generation failed")
        raise HTTPException(
            status_code=503,
            detail="Meme generation service temporarily unavailable",
            headers={"Retry-After": "30"},
        ) from exc
