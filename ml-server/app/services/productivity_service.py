import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from app.config import settings
from app.schemas.productivity import ActivityItem, ProductivityResult
from app.services.claude_service import claude_service

logger = logging.getLogger(__name__)

_prompt: str = ""


def _load_prompt() -> str:
    global _prompt
    if not _prompt:
        _prompt = (settings.prompts_dir / "productivity.txt").read_text(encoding="utf-8")
    return _prompt


def _compute_basic_metrics(activities: list[ActivityItem]) -> dict:
    """Calculate basic productivity metrics from raw activity data."""
    commits: list[ActivityItem] = []
    messages: list[ActivityItem] = []
    meetings: list[ActivityItem] = []

    for a in activities:
        t = a.type.lower()
        if t in ("commit", "push", "pull_request", "merge"):
            commits.append(a)
        elif t in ("message", "chat", "comment"):
            messages.append(a)
        elif t in ("meeting", "call", "standup"):
            meetings.append(a)

    # Group by date to calculate daily averages
    dates: set[str] = set()
    for a in activities:
        try:
            dt = datetime.fromisoformat(a.datetime.replace("Z", "+00:00"))
            dates.add(dt.strftime("%Y-%m-%d"))
        except (ValueError, AttributeError):
            pass

    num_days = max(len(dates), 1)
    total = max(len(activities), 1)

    return {
        "avg_commits_per_day": round(len(commits) / num_days, 2),
        "avg_commit_size": round(len(commits) / max(num_days, 1), 2),
        "message_frequency": round(len(messages) / num_days, 2),
        "meetings_ratio": round(len(meetings) / total, 2),
        "total_activities": len(activities),
        "num_days": num_days,
    }


async def analyze_productivity(
    employee_id: str, activities: list[ActivityItem]
) -> ProductivityResult:
    """Analyze productivity from activity data."""
    system_prompt = _load_prompt()
    metrics = _compute_basic_metrics(activities)

    user_message = json.dumps(
        {"employee_id": employee_id, "metrics": metrics},
        ensure_ascii=False,
    )

    logger.info("Analyzing productivity for employee=%s, activities=%d", employee_id, len(activities))
    raw: Any = await claude_service.analyze_json(system_prompt, user_message)

    return ProductivityResult(**raw)
