import json
import logging
from typing import Any

from app.config import settings
from app.schemas.sentiment import SentimentResult, TextItem
from app.services.claude_service import claude_service

logger = logging.getLogger(__name__)

_prompt: str = ""


def _load_prompt() -> str:
    global _prompt
    if not _prompt:
        _prompt = (settings.prompts_dir / "sentiment.txt").read_text(encoding="utf-8")
    return _prompt


async def analyze_sentiment(texts: list[TextItem]) -> list[SentimentResult]:
    """Analyze sentiment for a batch of texts via Claude."""
    system_prompt = _load_prompt()

    user_message = json.dumps(
        [{"id": t.id, "text": t.text} for t in texts],
        ensure_ascii=False,
    )

    logger.info("Analyzing sentiment for %d texts", len(texts))
    raw: Any = await claude_service.analyze_json(system_prompt, user_message)

    results: list[SentimentResult] = []
    for item in raw:
        results.append(SentimentResult(**item))

    return results
