import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.collectors.telegram import TelegramCollector, MAPPINGS_PATH
from app.schemas.activity import ActivityType, ActivitySource


@pytest.fixture
def mock_mappings(tmp_path):
    mappings = {
        "telegram_username_to_email": {
            "@ivanov_dev": "ivanov@company.com",
            "@petrova_pm": "petrova@company.com",
        }
    }
    mappings_file = tmp_path / "user_mappings.json"
    mappings_file.write_text(json.dumps(mappings))
    return mappings_file


@pytest.fixture
def telegram_collector(mock_mappings):
    with patch("app.collectors.telegram.MAPPINGS_PATH", mock_mappings), \
         patch("app.collectors.telegram.Bot"):
        collector = TelegramCollector()
        return collector


class TestResolveEmail:
    def test_known_username_with_at(self, telegram_collector):
        assert telegram_collector.resolve_email("@ivanov_dev") == "ivanov@company.com"

    def test_known_username_without_at(self, telegram_collector):
        assert telegram_collector.resolve_email("ivanov_dev") == "ivanov@company.com"

    def test_unknown_username(self, telegram_collector):
        assert telegram_collector.resolve_email("@unknown_user") is None

    def test_none_username(self, telegram_collector):
        assert telegram_collector.resolve_email(None) is None

    def test_empty_username(self, telegram_collector):
        assert telegram_collector.resolve_email("") is None


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_process_valid_message(self, telegram_collector):
        message = MagicMock()
        message.text = "Hello, team!"
        message.from_user = MagicMock()
        message.from_user.username = "ivanov_dev"
        message.date = datetime(2026, 3, 23, 14, 30, 0, tzinfo=timezone.utc)

        with patch("app.collectors.telegram.backend_client") as mock_client:
            mock_client.send_activity = AsyncMock(return_value=True)
            await telegram_collector.process_message(message)

            mock_client.send_activity.assert_called_once()
            activity = mock_client.send_activity.call_args[0][0]

            assert activity.employee_email == "ivanov@company.com"
            assert activity.type == ActivityType.MESSAGE
            assert activity.source == ActivitySource.TELEGRAM
            assert activity.data["text"] == "Hello, team!"

    @pytest.mark.asyncio
    async def test_process_message_unknown_user_ignored(self, telegram_collector):
        message = MagicMock()
        message.text = "Some message"
        message.from_user = MagicMock()
        message.from_user.username = "unknown_person"

        with patch("app.collectors.telegram.backend_client") as mock_client:
            mock_client.send_activity = AsyncMock()
            await telegram_collector.process_message(message)

            mock_client.send_activity.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_no_text_ignored(self, telegram_collector):
        message = MagicMock()
        message.text = None
        message.from_user = MagicMock()
        message.from_user.username = "ivanov_dev"

        with patch("app.collectors.telegram.backend_client") as mock_client:
            mock_client.send_activity = AsyncMock()
            await telegram_collector.process_message(message)

            mock_client.send_activity.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_backend_failure_queues_retry(self, telegram_collector):
        message = MagicMock()
        message.text = "Important message"
        message.from_user = MagicMock()
        message.from_user.username = "ivanov_dev"
        message.date = datetime(2026, 3, 23, 14, 30, 0, tzinfo=timezone.utc)

        with patch("app.collectors.telegram.backend_client") as mock_client, \
             patch.object(telegram_collector, "_queue_for_retry") as mock_queue:
            mock_client.send_activity = AsyncMock(side_effect=Exception("Connection refused"))
            await telegram_collector.process_message(message)

            mock_queue.assert_called_once()
            activity = mock_queue.call_args[0][0]
            assert activity.employee_email == "ivanov@company.com"
            assert activity.data["text"] == "Important message"


class TestMappingsLoading:
    def test_mappings_loaded_from_file(self, telegram_collector):
        assert len(telegram_collector._username_to_email) == 2
        assert telegram_collector._username_to_email["@ivanov_dev"] == "ivanov@company.com"

    def test_missing_mappings_file_handled(self):
        with patch("app.collectors.telegram.MAPPINGS_PATH", "/nonexistent/path.json"), \
             patch("app.collectors.telegram.Bot"):
            collector = TelegramCollector()
            assert collector._username_to_email == {}


class TestActivityUnitSerialization:
    def test_message_activity_to_request_dict(self):
        from app.schemas.activity import ActivityUnit, MessageData

        activity = ActivityUnit(
            employee_email="ivanov@company.com",
            type=ActivityType.MESSAGE,
            source=ActivitySource.TELEGRAM,
            datetime=datetime(2026, 3, 23, 14, 30, tzinfo=timezone.utc),
            data=MessageData(text="Hello!").model_dump(),
        )
        d = activity.to_request_dict()
        assert d["type"] == "message"
        assert d["source"] == "telegram"
        assert d["data"]["text"] == "Hello!"
        assert d["employee_email"] == "ivanov@company.com"
