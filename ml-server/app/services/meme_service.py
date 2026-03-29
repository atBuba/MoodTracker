"""Meme generation service using OpenRouter.

Pipeline:
1. Generate meme caption via LLM (google/gemini-3-flash-preview)
2. Generate image via image model (sourceful/riverflow-v2-pro)
3. Upload image to MinIO
4. Return URL

Fallback: backend random content → placeholder URL.
"""

import base64
import logging

import httpx

from app.config import settings
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)


async def generate_meme(context: str) -> str:
    """Generate a meme image and return its URL.

    Fallback chain:
    1. OpenRouter image generation (Riverflow)
    2. Backend random content endpoint
    3. Text-based placeholder
    """
    # Step 1: Generate caption via LLM
    try:
        caption = await _generate_caption(context)
    except Exception:
        logger.exception("Caption generation failed, using context as caption")
        caption = context

    # Step 2: Generate image via Riverflow
    try:
        image_url = await _generate_image(caption)
        if image_url:
            return image_url
    except Exception:
        logger.exception("Image generation failed, trying fallback")

    # Step 3: Backend random meme
    try:
        url = await _fetch_from_backend()
        if url:
            return url
    except Exception:
        logger.exception("Backend fallback failed, using placeholder")

    # Step 4: Placeholder
    return "https://placehold.co/512x512/EEE/31343C?text=Stay+positive!"


async def _generate_caption(context: str) -> str:
    """Generate a short meme caption using LLM via OpenRouter."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_llm_model,
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты создаёшь короткие мотивационные подписи для мемов. "
                            "Отвечай ТОЛЬКО текстом подписи, без кавычек и пояснений. "
                            "1-2 предложения, позитивный тон, можно с юмором."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Создай подпись для мотивац��онного мема. Контекст: {context}",
                    },
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        caption = data["choices"][0]["message"]["content"].strip()
        logger.info("Generated meme caption: %s", caption[:80])
        return caption


async def _generate_image(caption: str) -> str | None:
    """Generate an image via OpenRouter image model (Riverflow)."""
    prompt = (
        f"Motivational corporate meme, colorful and positive, "
        f"cartoon style, no text on image. Theme: {caption}"
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_image_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

        # OpenRouter image models return base64 in content or a URL
        choice = data["choices"][0]["message"]
        content = choice.get("content", "")

        # Check if response contains image URL
        if content.startswith("http"):
            img_response = await client.get(content, timeout=30.0)
            img_response.raise_for_status()
            image_bytes = img_response.content
            content_type = img_response.headers.get("content-type", "image/png")
        elif "data:image" in content or _is_base64(content):
            # Strip data URI prefix if present
            b64_data = content
            if "base64," in b64_data:
                b64_data = b64_data.split("base64,", 1)[1]
            image_bytes = base64.b64decode(b64_data)
            content_type = "image/png"
        else:
            logger.warning("Unexpected image response format: %s", content[:200])
            return None

        uploaded_url = await minio_service.upload_image(image_bytes, content_type)
        logger.info("Generated and uploaded meme image to MinIO")
        return uploaded_url


def _is_base64(s: str) -> bool:
    """Quick check if string looks like base64-encoded data."""
    if len(s) < 100:
        return False
    try:
        base64.b64decode(s[:100], validate=True)
        return True
    except Exception:
        return False


async def _fetch_from_backend() -> str | None:
    """Fetch a random meme URL from the backend service."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.backend_url}/api/internal/random-content",
            params={"type": "meme"},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("url") or data.get("image_url")
