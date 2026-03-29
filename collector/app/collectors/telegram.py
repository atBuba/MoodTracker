import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from app.config import settings
from app.collectors.base import BaseCollector
from app.schemas.activity import ActivitySource, ActivityType, ActivityUnit, MessageData
from app.services.backend_client import backend_client

logger = logging.getLogger(__name__)

MAPPINGS_PATH = Path(__file__).parent.parent / "mappings" / "user_mappings.json"


class TelegramCollector(BaseCollector):
    def __init__(self) -> None:
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self._username_to_email: dict[str, str] = {}
        self._load_mappings()
        self._register_handlers()

    def _load_mappings(self) -> None:
        try:
            with open(MAPPINGS_PATH) as f:
                data = json.load(f)
            self._username_to_email = data.get("telegram_username_to_email", {})
            logger.info(
                "Loaded %d Telegram username mappings", len(self._username_to_email)
            )
        except FileNotFoundError:
            logger.warning("User mappings file not found at %s", MAPPINGS_PATH)
        except Exception:
            logger.exception("Failed to load user mappings")

    async def refresh_mappings_from_backend(self) -> None:
        """Fetch fresh mappings from the backend."""
        try:
            url = f"{settings.BACKEND_URL}/api/internal/employee-mappings"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"X-Internal-Api-Key": settings.INTERNAL_API_KEY},
                )
                response.raise_for_status()
                data = response.json()
                if "telegram_username_to_email" in data:
                    self._username_to_email.update(data["telegram_username_to_email"])
                    logger.info(
                        "Refreshed mappings from backend, total: %d",
                        len(self._username_to_email),
                    )
        except Exception:
            logger.exception("Failed to refresh mappings from backend")

    def resolve_email(self, username: str | None) -> str | None:
        if not username:
            return None
        normalized = f"@{username}" if not username.startswith("@") else username
        return self._username_to_email.get(normalized)

    def _register_handlers(self) -> None:
        @self.dp.message(CommandStart())
        async def handle_start(message: types.Message) -> None:
            await message.answer(
                "BurnOutDetector Collector bot is active. Your messages are being tracked."
            )

        @self.dp.message()
        async def handle_message(message: types.Message) -> None:
            await self.process_message(message)

    async def process_message(self, message: types.Message) -> None:
        if not message.text:
            return

        username = message.from_user.username if message.from_user else None
        email = self.resolve_email(username)

        if not email:
            logger.debug(
                "Ignoring message from unmapped user: %s",
                username or "unknown",
            )
            return

        activity = ActivityUnit(
            employee_email=email,
            type=ActivityType.MESSAGE,
            source=ActivitySource.TELEGRAM,
            datetime=message.date or datetime.now(timezone.utc),
            data=MessageData(text=message.text).model_dump(),
        )

        try:
            await backend_client.send_activity(activity)
        except Exception:
            logger.exception(
                "Failed to send Telegram message to backend, queuing for retry"
            )
            self._queue_for_retry(activity)

    def _queue_for_retry(self, activity: ActivityUnit) -> None:
        """Queue failed activity for later retry via Celery/RabbitMQ."""
        try:
            from app.celery_app import celery_app

            celery_app.send_task(
                "app.tasks.retry_tasks.retry_send_activity",
                args=[activity.to_request_dict()],
                queue="retry",
            )
            logger.info("Queued activity for retry via RabbitMQ")
        except Exception:
            logger.exception("Failed to queue activity for retry")

    async def collect(self, since: datetime) -> list[ActivityUnit]:
        """Not used for Telegram -- messages are processed in real-time via long polling."""
        return []

    async def start_polling(self) -> None:
        logger.info("Starting Telegram bot long polling")
        await self.refresh_mappings_from_backend()
        await self.dp.start_polling(self.bot, handle_signals=False)

    async def stop_polling(self) -> None:
        logger.info("Stopping Telegram bot")
        await self.dp.stop_polling()
        await self.bot.session.close()
