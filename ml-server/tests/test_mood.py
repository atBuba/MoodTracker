from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.analysis import AnalyzeData
from app.schemas.productivity import ProductivityResult, Trend
from app.schemas.sentiment import Emotion, SentimentResult
from app.services.mood_service import analyze_mood


class TestMoodAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_mood_orchestration(self):
        """Test that mood analysis correctly orchestrates sentiment + productivity + Claude."""
        mock_sentiment_results = [
            SentimentResult(
                id="a1",
                positive_ratio=0.7,
                neutral_ratio=0.2,
                negative_ratio=0.1,
                emotion=Emotion.JOY,
            ),
        ]
        mock_productivity_result = ProductivityResult(
            productivity_score=0.8,
            patterns=["Высокая частота коммитов", "Стабильная активность"],
            trend=Trend.IMPROVING,
        )
        mock_claude_response = {
            "mood_index": 0.75,
            "analysis_summary": "Сотрудник демонстрирует хороший уровень вовлеченности.",
            "recommendations": ["Продолжить текущий режим работы"],
        }

        with (
            patch(
                "app.services.mood_service.analyze_sentiment",
                new_callable=AsyncMock,
                return_value=mock_sentiment_results,
            ),
            patch(
                "app.services.mood_service.analyze_productivity",
                new_callable=AsyncMock,
                return_value=mock_productivity_result,
            ),
            patch(
                "app.services.mood_service.claude_service"
            ) as mock_claude,
        ):
            mock_claude.analyze_json = AsyncMock(return_value=mock_claude_response)

            activities = [
                {
                    "id": "a1",
                    "type": "commit",
                    "source": "github",
                    "datetime": "2026-03-28T10:00:00Z",
                },
            ]
            result = await analyze_mood("emp-123", activities)

            assert isinstance(result, AnalyzeData)
            assert result.mood_index == 0.75
            assert "вовлеченности" in result.summary
            assert "Рекомендации" in result.summary

    @pytest.mark.asyncio
    async def test_analyze_mood_returns_correct_format(self):
        """Test that the response matches the backend contract: {mood_index, summary}."""
        mock_claude_response = {
            "mood_index": 0.5,
            "analysis_summary": "Средний уровень.",
            "recommendations": [],
        }

        with (
            patch(
                "app.services.mood_service.analyze_sentiment",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "app.services.mood_service.analyze_productivity",
                new_callable=AsyncMock,
                return_value=ProductivityResult(
                    productivity_score=0.5,
                    patterns=[],
                    trend=Trend.STABLE,
                ),
            ),
            patch(
                "app.services.mood_service.claude_service"
            ) as mock_claude,
        ):
            mock_claude.analyze_json = AsyncMock(return_value=mock_claude_response)

            result = await analyze_mood("emp-456", [])

            assert hasattr(result, "mood_index")
            assert hasattr(result, "summary")
            assert isinstance(result.mood_index, float)
            assert isinstance(result.summary, str)
