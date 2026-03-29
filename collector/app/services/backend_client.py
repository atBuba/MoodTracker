import logging

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.schemas.activity import ActivityUnit

logger = logging.getLogger(__name__)

BACKEND_ACTIVITY_URL = f"{settings.BACKEND_URL}/api/internal/activity"
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 5


class BackendClient:
    def __init__(self) -> None:
        self._headers = {
            "X-Internal-Api-Key": settings.INTERNAL_API_KEY,
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        reraise=True,
    )
    async def send_activity(self, activity: ActivityUnit) -> bool:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                BACKEND_ACTIVITY_URL,
                json=activity.to_request_dict(),
                headers=self._headers,
            )
            response.raise_for_status()
            logger.info(
                "Sent activity to backend: type=%s source=%s email=%s",
                activity.type.value,
                activity.source.value,
                activity.employee_email,
            )
            return True

    async def send_activities(self, activities: list[ActivityUnit]) -> int:
        sent = 0
        for activity in activities:
            try:
                await self.send_activity(activity)
                sent += 1
            except Exception:
                logger.exception(
                    "Failed to send activity after retries: type=%s source=%s email=%s",
                    activity.type.value,
                    activity.source.value,
                    activity.employee_email,
                )
        return sent

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        reraise=True,
    )
    async def send_activity_dict(self, payload: dict) -> bool:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                BACKEND_ACTIVITY_URL,
                json=payload,
                headers=self._headers,
            )
            response.raise_for_status()
            return True


backend_client = BackendClient()
