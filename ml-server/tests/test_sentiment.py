import json
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.sentiment import Emotion, SentimentResult, TextItem
from app.services.claude_service import ClaudeService
from app.services.sentiment_service import analyze_sentiment


class TestSentimentSchemas:
    def test_sentiment_result_valid(self):
        result = SentimentResult(
            id="msg-1",
            positive_ratio=0.7,
            neutral_ratio=0.2,
            negative_ratio=0.1,
            emotion=Emotion.JOY,
        )
        assert result.positive_ratio == 0.7
        assert result.emotion == Emotion.JOY

    def test_sentiment_result_boundary_values(self):
        result = SentimentResult(
            id="msg-2",
            positive_ratio=0.0,
            neutral_ratio=0.0,
            negative_ratio=1.0,
            emotion=Emotion.ANGER,
        )
        assert result.negative_ratio == 1.0

    def test_text_item(self):
        item = TextItem(id="t1", text="Hello world")
        assert item.id == "t1"
        assert item.text == "Hello world"


class TestClaudeJsonExtraction:
    def test_extract_plain_json(self):
        raw = '[{"id": "1", "positive_ratio": 0.8, "neutral_ratio": 0.1, "negative_ratio": 0.1, "emotion": "joy"}]'
        result = ClaudeService._extract_json(raw)
        assert isinstance(result, list)
        assert result[0]["emotion"] == "joy"

    def test_extract_fenced_json(self):
        raw = '```json\n[{"id": "1", "positive_ratio": 0.5, "neutral_ratio": 0.3, "negative_ratio": 0.2, "emotion": "neutral"}]\n```'
        result = ClaudeService._extract_json(raw)
        assert isinstance(result, list)
        assert result[0]["positive_ratio"] == 0.5

    def test_extract_fenced_no_lang(self):
        raw = '```\n{"key": "value"}\n```'
        result = ClaudeService._extract_json(raw)
        assert result["key"] == "value"


class TestSentimentService:
    @pytest.mark.asyncio
    async def test_analyze_sentiment_mock(self):
        mock_response = [
            {
                "id": "msg-1",
                "positive_ratio": 0.6,
                "neutral_ratio": 0.3,
                "negative_ratio": 0.1,
                "emotion": "joy",
            },
            {
                "id": "msg-2",
                "positive_ratio": 0.1,
                "neutral_ratio": 0.2,
                "negative_ratio": 0.7,
                "emotion": "anger",
            },
        ]

        with patch(
            "app.services.sentiment_service.claude_service"
        ) as mock_claude:
            mock_claude.analyze_json = AsyncMock(return_value=mock_response)

            texts = [
                TextItem(id="msg-1", text="Great work everyone!"),
                TextItem(id="msg-2", text="This is frustrating."),
            ]
            results = await analyze_sentiment(texts)

            assert len(results) == 2
            assert results[0].id == "msg-1"
            assert results[0].emotion == Emotion.JOY
            assert results[1].negative_ratio == 0.7
