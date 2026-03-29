import json
import logging
from typing import Any

from app.config import settings
from app.schemas.analysis import AnalyzeData
from app.schemas.productivity import ActivityItem as ProdActivity
from app.schemas.sentiment import TextItem
from app.services.claude_service import claude_service
from app.services.productivity_service import analyze_productivity
from app.services.sentiment_service import analyze_sentiment

logger = logging.getLogger(__name__)

_prompt: str = ""


def _load_prompt() -> str:
    global _prompt
    if not _prompt:
        _prompt = (settings.prompts_dir / "mood_analysis.txt").read_text(encoding="utf-8")
    return _prompt


async def analyze_mood(employee_id: str, activities: list[dict]) -> AnalyzeData:
    """Run full mood analysis: sentiment + productivity -> Claude mood_index.

    Returns AnalyzeData with mood_index and summary matching the backend contract.
    """
    # Convert activities for productivity analysis
    prod_activities = [ProdActivity(**a) for a in activities]

    # Build pseudo-texts from activities for sentiment (use type + source as text)
    sentiment_texts = [
        TextItem(id=a["id"], text=f"{a['type']} from {a['source']} at {a['datetime']}")
        for a in activities
    ]

    # Run sentiment and productivity in parallel-ish fashion
    sentiment_results = await analyze_sentiment(sentiment_texts) if sentiment_texts else []
    productivity_result = await analyze_productivity(employee_id, prod_activities)

    # Aggregate sentiment
    if sentiment_results:
        avg_positive = sum(r.positive_ratio for r in sentiment_results) / len(sentiment_results)
        avg_neutral = sum(r.neutral_ratio for r in sentiment_results) / len(sentiment_results)
        avg_negative = sum(r.negative_ratio for r in sentiment_results) / len(sentiment_results)
    else:
        avg_positive = 0.5
        avg_neutral = 0.5
        avg_negative = 0.0

    # Prepare data for final Claude analysis
    system_prompt = _load_prompt()
    combined_data = {
        "employee_id": employee_id,
        "sentiment": {
            "avg_positive": round(avg_positive, 3),
            "avg_neutral": round(avg_neutral, 3),
            "avg_negative": round(avg_negative, 3),
            "sample_count": len(sentiment_results),
        },
        "productivity": {
            "score": productivity_result.productivity_score,
            "patterns": productivity_result.patterns,
            "trend": productivity_result.trend.value,
        },
    }

    user_message = json.dumps(combined_data, ensure_ascii=False)
    logger.info("Running final mood analysis for employee=%s", employee_id)
    raw: Any = await claude_service.analyze_json(system_prompt, user_message)

    mood_index: float = float(raw["mood_index"])
    analysis_summary: str = raw.get("analysis_summary", "")
    recommendations: list[str] = raw.get("recommendations", [])

    # Build the summary string that the backend expects
    summary_parts = [analysis_summary]
    if recommendations:
        summary_parts.append("Рекомендации: " + "; ".join(recommendations))
    summary = " ".join(summary_parts)

    return AnalyzeData(mood_index=mood_index, summary=summary)
