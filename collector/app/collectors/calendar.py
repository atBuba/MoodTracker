import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.collectors.base import BaseCollector
from app.config import settings
from app.schemas.activity import ActivitySource, ActivityType, ActivityUnit, EventData

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "collector:calendar:last_check"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class CalendarCollector(BaseCollector):
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self._service = None

    def _get_calendar_service(self):
        if self._service is None:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
            )
            self._service = build("calendar", "v3", credentials=credentials)
        return self._service

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return self._redis

    async def _get_last_check(self, calendar_id: str) -> datetime:
        r = await self._get_redis()
        key = f"{REDIS_KEY_PREFIX}:{calendar_id}"
        val = await r.get(key)
        if val:
            return datetime.fromisoformat(val)
        return datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )

    async def _set_last_check(self, calendar_id: str, dt: datetime) -> None:
        r = await self._get_redis()
        key = f"{REDIS_KEY_PREFIX}:{calendar_id}"
        await r.set(key, dt.isoformat())

    @staticmethod
    def _parse_event_datetime(event_dt: dict) -> datetime | None:
        """Parse dateTime or date from a Google Calendar event start/end."""
        if "dateTime" in event_dt:
            return datetime.fromisoformat(event_dt["dateTime"])
        if "date" in event_dt:
            return datetime.fromisoformat(event_dt["date"]).replace(
                tzinfo=timezone.utc
            )
        return None

    def _fetch_events(
        self, calendar_id: str, time_min: datetime
    ) -> list[dict]:
        service = self._get_calendar_service()
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                maxResults=250,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    async def collect(self, since: datetime) -> list[ActivityUnit]:
        all_activities: list[ActivityUnit] = []

        for calendar_id in settings.google_calendar_ids_list:
            try:
                last_check = await self._get_last_check(calendar_id)
                events = self._fetch_events(calendar_id, last_check)

                latest_dt = last_check
                for event in events:
                    organizer = event.get("organizer", {})
                    email = (
                        event.get("creator", {}).get("email")
                        or organizer.get("email")
                        or ""
                    )
                    if not email:
                        continue

                    start = self._parse_event_datetime(event.get("start", {}))
                    end = self._parse_event_datetime(event.get("end", {}))

                    duration_hours = 0.0
                    if start and end:
                        delta = end - start
                        duration_hours = round(delta.total_seconds() / 3600, 2)

                    event_dt = start or datetime.now(timezone.utc)

                    activity = ActivityUnit(
                        employee_email=email,
                        type=ActivityType.EVENT,
                        source=ActivitySource.GOOGLE_CALENDAR,
                        datetime=event_dt,
                        data=EventData(
                            name=event.get("summary", "Untitled"),
                            text=event.get("description", ""),
                            duration_hours=duration_hours,
                        ).model_dump(),
                    )
                    all_activities.append(activity)

                    if event_dt > latest_dt:
                        latest_dt = event_dt

                if events:
                    await self._set_last_check(calendar_id, latest_dt)

                logger.info(
                    "Collected %d events from calendar %s",
                    len(events),
                    calendar_id,
                )
            except Exception:
                logger.exception(
                    "Failed to collect events from calendar %s", calendar_id
                )

        return all_activities

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
