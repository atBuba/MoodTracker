"""Mock data collector for testing without real external APIs.

Generates realistic fake activity data (messages, commits, comments, events)
and sends them to the backend, simulating all three real collectors.
"""

import logging
import random
from datetime import datetime, timedelta, timezone

from app.collectors.base import BaseCollector
from app.schemas.activity import (
    ActivitySource,
    ActivityType,
    ActivityUnit,
    CommentData,
    CommitData,
    EventData,
    MessageData,
)

logger = logging.getLogger(__name__)

# Mock employees — these emails must exist in the backend DB
MOCK_EMPLOYEES = [
    "ivanov@company.com",
    "petrova@company.com",
    "sidorov@company.com",
]

MOCK_MESSAGES = [
    "Привет, коллеги! Как продвигается задача?",
    "Закончил ревью, всё выглядит хорошо",
    "Есть вопрос по архитектуре — давайте обсудим",
    "Сегодня закрою таску по рефакторингу",
    "Не могу разобраться с этим багом, уже третий час сижу...",
    "Отличная работа, спасибо за помощь!",
    "Кто-нибудь может помочь с деплоем?",
    "Устал сегодня, пойду пораньше",
    "Мерж-конфликт опять... ненавижу понедельники",
    "Ура, спринт закрыт! Идём на обед?",
    "Встреча затянулась, не успеваю по таске",
    "Кажется, нашёл решение — сейчас запушу",
    "Всё работает, тесты зелёные!",
    "Нужен отпуск... срочно",
    "Классный митап был вчера, рекомендую записи посмотреть",
]

MOCK_COMMIT_TITLES = [
    "feat: add user profile page",
    "fix: resolve null pointer in auth module",
    "refactor: simplify database queries",
    "chore: update dependencies",
    "feat: implement notification system",
    "fix: correct date formatting bug",
    "feat: add export to CSV feature",
    "fix: handle edge case in payment processing",
    "docs: update API documentation",
    "test: add integration tests for auth",
]

MOCK_COMMIT_DESCRIPTIONS = [
    "Implemented the user profile with avatar support.",
    "Fixed edge case when user token is expired.",
    "Simplified complex joins into cleaner ORM queries.",
    "",
    "Added push and email notification channels.",
    "Fixed locale-specific date parsing issues.",
    "",
    "Handle null amount gracefully.",
    "Updated swagger docs for v2 endpoints.",
    "Added tests covering OAuth flow.",
]

MOCK_PR_COMMENTS = [
    "LGTM, но можно ли упростить этот блок?",
    "Отличное решение!",
    "Нужно добавить обработку ошибок тут",
    "А что если передать null? Тест есть?",
    "Предлагаю вынести в отдельный метод",
    "Хорошо, одобряю",
    "Пожалуйста, добавь комментарий к этому хаку",
]

MOCK_EVENTS = [
    ("Sprint Planning", "Планирование спринта 24", 1.5),
    ("Daily Standup", "Ежедневный стендап команды", 0.25),
    ("1-on-1 с менеджером", "Еженедельная встреча", 0.5),
    ("Code Review Session", "Групповое ревью архитектуры", 1.0),
    ("Ретроспектива", "Ретро спринта 23", 1.0),
    ("Обед с командой", "", 1.0),
    ("Tech Talk: Микросервисы", "Внутренний доклад", 0.75),
]


class MockCollector(BaseCollector):
    """Generates fake activity data for testing the full pipeline."""

    async def collect(self, since: datetime) -> list[ActivityUnit]:
        activities: list[ActivityUnit] = []
        now = datetime.now(timezone.utc)

        for email in MOCK_EMPLOYEES:
            # Generate 2-5 messages per employee
            for _ in range(random.randint(2, 5)):
                dt = now - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
                activities.append(
                    ActivityUnit(
                        employee_email=email,
                        type=ActivityType.MESSAGE,
                        source=ActivitySource.TELEGRAM,
                        datetime=dt,
                        data=MessageData(
                            text=random.choice(MOCK_MESSAGES)
                        ).model_dump(),
                    )
                )

            # Generate 1-3 commits per employee
            for i in range(random.randint(1, 3)):
                idx = random.randint(0, len(MOCK_COMMIT_TITLES) - 1)
                dt = now - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
                activities.append(
                    ActivityUnit(
                        employee_email=email,
                        type=ActivityType.COMMIT,
                        source=ActivitySource.GITHUB,
                        datetime=dt,
                        data=CommitData(
                            title=MOCK_COMMIT_TITLES[idx],
                            description=MOCK_COMMIT_DESCRIPTIONS[idx],
                            lines_added=random.randint(5, 200),
                            lines_deleted=random.randint(0, 50),
                        ).model_dump(),
                    )
                )

            # Generate 0-2 PR comments per employee
            for _ in range(random.randint(0, 2)):
                dt = now - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
                activities.append(
                    ActivityUnit(
                        employee_email=email,
                        type=ActivityType.COMMENT,
                        source=ActivitySource.GITHUB,
                        datetime=dt,
                        data=CommentData(
                            text=random.choice(MOCK_PR_COMMENTS)
                        ).model_dump(),
                    )
                )

            # Generate 1-2 calendar events per employee
            for _ in range(random.randint(1, 2)):
                event = random.choice(MOCK_EVENTS)
                dt = now - timedelta(
                    hours=random.randint(0, 8),
                    minutes=random.choice([0, 15, 30, 45]),
                )
                activities.append(
                    ActivityUnit(
                        employee_email=email,
                        type=ActivityType.EVENT,
                        source=ActivitySource.GOOGLE_CALENDAR,
                        datetime=dt,
                        data=EventData(
                            name=event[0],
                            text=event[1],
                            duration_hours=event[2],
                        ).model_dump(),
                    )
                )

        logger.info(
            "MockCollector generated %d activities for %d employees",
            len(activities),
            len(MOCK_EMPLOYEES),
        )
        return activities
