"""
Rich seed script — populates the database with 30 days of realistic mock data
so that dashboards, charts, and notifications look complete.
"""

import asyncio
import math
import random
import sys
import os
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete

from app.database import async_session_maker, engine, Base
from app.models import *  # noqa: F401,F403
from app.models.team import Team
from app.models.employee import Employee, RoleEnum
from app.models.activity import ActivityUnit, ActivityTypeEnum, Message, Commit, Comment, Event
from app.models.sentiment import Sentiment
from app.models.employee_state import EmployeeState
from app.models.notification import Notification, NotificationTypeEnum
from app.models.motivation_content import MotivationContent, MotivationTypeEnum
from app.models.manager_settings import ManagerSetting, NotificationPeriodEnum
from app.services.auth_service import get_password_hash

# ──────────────────────────────────────────────────────────────────
# Data pools
# ──────────────────────────────────────────────────────────────────

MESSAGES_POSITIVE = [
    "Отличная работа, ребята! Спринт закрыт досрочно!",
    "Наконец-то разобрался с этим модулем — всё работает как часы!",
    "Спасибо за ревью, очень полезные комментарии!",
    "Сегодня продуктивный день, закрыл 5 тасок",
    "Кайф, тесты все зелёные с первого раза!",
    "Классный митап был, много полезного узнал",
    "Команда топ, спасибо за поддержку!",
    "Деплой прошёл гладко, ни одного бага в проде",
    "Ура, получил повышение! Спасибо всем!",
    "Обожаю работать с этой командой",
]

MESSAGES_NEUTRAL = [
    "Привет, коллеги! Как продвигается задача?",
    "Сегодня работаю из дома",
    "Созвон в 15:00, не забудьте",
    "Обновил документацию по API",
    "Кто-нибудь может посмотреть мой PR?",
    "Переключаюсь на задачу по фронтенду",
    "Пушнул фикс, посмотрите когда будет время",
    "Стендап через 10 минут",
    "Ушёл на обед, буду через час",
    "Залил изменения в staging",
]

MESSAGES_NEGATIVE = [
    "Этот баг уже третий день не могу починить, всё бесит...",
    "Мерж-конфликт опять, ненавижу понедельники",
    "Устал, не высыпаюсь совсем",
    "Встреча за встречей, когда кодить-то?",
    "Опять сломали прод после деплоя...",
    "Не понимаю, зачем мы это переписываем",
    "Дедлайн горит, а задач только прибавляется",
    "Тесты падают на CI, локально всё ок — бесит",
    "Нужен отпуск... срочно",
    "Чувствую себя выгоревшим",
]

COMMIT_TITLES = [
    "feat: add user profile page",
    "fix: resolve null pointer in auth module",
    "refactor: simplify database queries",
    "chore: update dependencies to latest versions",
    "feat: implement notification system",
    "fix: correct date formatting bug",
    "feat: add export to CSV feature",
    "fix: handle edge case in payment processing",
    "docs: update API documentation",
    "test: add integration tests for auth flow",
    "feat: add dark mode support",
    "fix: memory leak in websocket handler",
    "refactor: extract common validation logic",
    "feat: implement real-time updates",
    "fix: resolve race condition in queue",
]

COMMIT_DESCRIPTIONS = [
    "Implemented the user profile with avatar support and settings panel.",
    "Fixed edge case when user token is expired and refresh fails.",
    "Simplified complex joins into cleaner ORM queries for better perf.",
    "",
    "Added push and email notification channels with templates.",
    "Fixed locale-specific date parsing issues across timezones.",
    "",
    "Handle null amount gracefully with proper error message.",
    "Updated swagger docs for v2 endpoints with examples.",
    "Added tests covering OAuth flow and token refresh.",
    "Added CSS variables for theme switching.",
    "Fixed connection pool not releasing on error.",
    "Moved shared validators to utils module.",
    "WebSocket integration for live dashboard updates.",
    "Added mutex lock for concurrent queue access.",
]

PR_COMMENTS = [
    "LGTM! Отличная работа.",
    "Нужно добавить обработку ошибок тут — что если сервер вернёт 500?",
    "Предлагаю вынести в отдельный сервис, чтобы не раздувать контроллер.",
    "А что если передать null? Добавь пожалуйста тест.",
    "Классное решение! Не подумал бы так сделать.",
    "Можно ли упростить этот блок? Слишком вложенная логика.",
    "Одобряю, мержи.",
    "Добавь комментарий, чтобы было понятно зачем этот хак.",
    "Тесты надо обновить после этих изменений.",
    "Выглядит хорошо, но давай обсудим подход на стендапе.",
]

EVENT_NAMES = [
    ("Sprint Planning", "Планирование спринта", 1.5),
    ("Daily Standup", "Ежедневный стендап команды", 0.25),
    ("1-on-1 с менеджером", "Еженедельная личная встреча", 0.5),
    ("Code Review Session", "Групповое ревью архитектуры", 1.0),
    ("Ретроспектива", "Ретро текущего спринта", 1.0),
    ("Tech Talk", "Внутренний технический доклад", 0.75),
    ("Sprint Demo", "Демо результатов спринта", 1.0),
    ("Architecture Review", "Обсуждение архитектурных решений", 1.5),
    ("Onboarding Meeting", "Встреча по онбордингу нового сотрудника", 0.5),
    ("Team Building", "Командное мероприятие", 2.0),
]

EMOTIONS = ["joy", "neutral", "sadness", "anger", "fear", "surprise", "disgust"]

ANALYSIS_TEMPLATES = {
    "excellent": [
        "Сотрудник демонстрирует высокий уровень вовлечённости и позитивный настрой. Активность в чатах и коде стабильно высокая, тональность общения преимущественно позитивная.",
        "Отличное эмоциональное состояние. Сотрудник активно участвует в командной работе, продуктивность на высоком уровне. Тренд стабильно положительный.",
    ],
    "good": [
        "Сотрудник в хорошем рабочем состоянии. Активность стабильная, тональность общения нейтрально-позитивная. Рекомендуется поддерживать текущий режим.",
        "Нормальное рабочее состояние с позитивным уклоном. Продуктивность на среднем уровне, эмоциональный фон ровный.",
    ],
    "normal": [
        "Состояние сотрудника в пределах нормы. Активность средняя, без выраженных отклонений. Стоит обратить внимание при снижении показателей.",
        "Эмоциональное состояние стабильное. Продуктивность и активность в рамках ожиданий. Специальных мер не требуется.",
    ],
    "attention": [
        "Наблюдается снижение настроения на протяжении последних дней. Тональность общения стала более негативной, частота коммитов снизилась. Рекомендуется обратить внимание.",
        "У сотрудника снижение эмоционального фона. Увеличилось количество негативных сообщений, продуктивность упала. Рекомендуется провести 1-on-1.",
    ],
    "critical": [
        "Критическое снижение настроения. Сотрудник практически не общается в чатах, продуктивность минимальная. Срочно рекомендуется провести беседу.",
        "Состояние сотрудника вызывает серьёзные опасения. Эмоциональный фон крайне негативный, активность резко снизилась. Необходимо вмешательство.",
    ],
}

RECOMMENDATIONS = [
    "Продолжить текущий режим работы",
    "Предложить сотруднику взять отгул или короткий отпуск",
    "Провести 1-on-1 встречу для обсуждения текущей нагрузки",
    "Рассмотреть перераспределение задач",
    "Предложить гибкий график на следующую неделю",
    "Уменьшить количество встреч для фокусировки на задачах",
    "Подключить к интересному проекту для повышения мотивации",
    "Отправить мотивационный контент",
    "Обсудить карьерные цели и перспективы",
    "Организовать командную активность для сплочения",
]

MOTIVATION_QUOTES = [
    "Единственный способ делать великую работу — любить то, что делаешь. — Стив Джобс",
    "Не бойся идти медленно, бойся стоять на месте.",
    "Каждый день — это новая возможность изменить свою жизнь.",
    "Успех — это не конечная точка, а путешествие.",
    "Лучший момент для начала — сейчас.",
    "Трудности делают нас сильнее.",
    "Верь в себя, и всё получится.",
    "Маленькие шаги ведут к большим переменам.",
    "Ошибки — это ступеньки к успеху.",
    "Команда — это сила. Вместе мы можем всё.",
]

MOTIVATION_SUGGESTIONS = [
    "Попробуйте сделать 5-минутную прогулку между задачами.",
    "Порадуйте себя чашкой любимого напитка!",
    "Сделайте перерыв и послушайте любимую музыку.",
    "Попробуйте технику Pomodoro: 25 минут работы, 5 минут отдыха.",
    "Выпейте стакан воды — гидратация важна для продуктивности.",
    "Проветрите комнату — свежий воздух помогает сосредоточиться.",
    "Напишите коллеге что-нибудь приятное — это поднимет настроение обоим!",
    "Закройте все лишние вкладки и сфокусируйтесь на одной задаче.",
]

MOTIVATION_MEMES = [
    "Когда баг починился сам, а ты даже не знаешь почему 🤔",
    "Пятница + зелёные тесты = счастье программиста",
    "Кот-программист верит в тебя!",
    "Когда код заработал с первого раза — не трогай!",
    "Ты молодец! Даже если CI так не считает.",
]

# ──────────────────────────────────────────────────────────────────
# Employee mood profiles (determines their 30-day mood trajectory)
# ──────────────────────────────────────────────────────────────────

EMPLOYEE_PROFILES = {
    "ivanov@company.com": {
        "name": "Иванов Иван",
        "position": "Backend Developer",
        "base_mood": 0.72,
        "trend": "stable",       # stable high performer
        "volatility": 0.08,
    },
    "petrova@company.com": {
        "name": "Петрова Мария",
        "position": "Frontend Developer",
        "base_mood": 0.80,
        "trend": "improving",    # getting happier
        "volatility": 0.06,
    },
    "sidorov@company.com": {
        "name": "Сидоров Алексей",
        "position": "QA Engineer",
        "base_mood": 0.55,
        "trend": "declining",    # declining mood — needs attention
        "volatility": 0.10,
    },
    "employee@burnoutdetector.com": {
        "name": "Козлова Елена",
        "position": "Software Engineer",
        "base_mood": 0.65,
        "trend": "wave",         # up and down
        "volatility": 0.12,
    },
}


def _mood_for_day(profile: dict, day_offset: int, total_days: int) -> float:
    """Generate a mood index for a specific day based on the profile."""
    base = profile["base_mood"]
    vol = profile["volatility"]
    trend = profile["trend"]
    t = day_offset / total_days  # 0.0 → 1.0

    if trend == "improving":
        base_shift = base + 0.15 * t
    elif trend == "declining":
        base_shift = base - 0.20 * t
    elif trend == "wave":
        base_shift = base + 0.12 * math.sin(t * math.pi * 3)
    else:  # stable
        base_shift = base

    noise = random.gauss(0, vol)
    mood = base_shift + noise
    return round(max(0.05, min(0.98, mood)), 2)


def _sentiment_from_mood(mood: float) -> tuple[float, float, float, str]:
    """Derive sentiment ratios and emotion from mood_index."""
    if mood >= 0.7:
        pos = round(random.uniform(0.55, 0.80), 2)
        neg = round(random.uniform(0.02, 0.10), 2)
        emotion = random.choice(["joy", "joy", "surprise", "neutral"])
    elif mood >= 0.5:
        pos = round(random.uniform(0.25, 0.45), 2)
        neg = round(random.uniform(0.10, 0.25), 2)
        emotion = random.choice(["neutral", "neutral", "joy"])
    elif mood >= 0.3:
        pos = round(random.uniform(0.08, 0.20), 2)
        neg = round(random.uniform(0.35, 0.55), 2)
        emotion = random.choice(["sadness", "fear", "neutral"])
    else:
        pos = round(random.uniform(0.0, 0.10), 2)
        neg = round(random.uniform(0.60, 0.85), 2)
        emotion = random.choice(["sadness", "anger", "disgust"])

    neu = round(1.0 - pos - neg, 2)
    neu = max(0.0, neu)
    return pos, neu, neg, emotion


def _analysis_for_mood(mood: float) -> str:
    if mood >= 0.7:
        return random.choice(ANALYSIS_TEMPLATES["excellent"])
    elif mood >= 0.55:
        return random.choice(ANALYSIS_TEMPLATES["good"])
    elif mood >= 0.45:
        return random.choice(ANALYSIS_TEMPLATES["normal"])
    elif mood >= 0.3:
        return random.choice(ANALYSIS_TEMPLATES["attention"])
    else:
        return random.choice(ANALYSIS_TEMPLATES["critical"])


def _pick_messages(mood: float, count: int) -> list[str]:
    """Pick messages weighted by mood."""
    msgs = []
    for _ in range(count):
        r = random.random()
        if mood >= 0.65:
            if r < 0.5:
                msgs.append(random.choice(MESSAGES_POSITIVE))
            elif r < 0.85:
                msgs.append(random.choice(MESSAGES_NEUTRAL))
            else:
                msgs.append(random.choice(MESSAGES_NEGATIVE))
        elif mood >= 0.4:
            if r < 0.2:
                msgs.append(random.choice(MESSAGES_POSITIVE))
            elif r < 0.65:
                msgs.append(random.choice(MESSAGES_NEUTRAL))
            else:
                msgs.append(random.choice(MESSAGES_NEGATIVE))
        else:
            if r < 0.1:
                msgs.append(random.choice(MESSAGES_POSITIVE))
            elif r < 0.35:
                msgs.append(random.choice(MESSAGES_NEUTRAL))
            else:
                msgs.append(random.choice(MESSAGES_NEGATIVE))
    return msgs


# ──────────────────────────────────────────────────────────────────
# Main seed
# ──────────────────────────────────────────────────────────────────

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables ensured.")

    async with async_session_maker() as session:
        # Wipe old data for clean re-seed
        for tbl in [
            Notification, EmployeeState, Sentiment,
            Message, Commit, Comment, Event, ActivityUnit,
            MotivationContent, ManagerSetting, Employee, Team,
        ]:
            await session.execute(delete(tbl))
        await session.flush()
        print("Old data cleared.")

        # ── Teams ─────────────────────────────────────────────
        team_eng = Team(name="Engineering", description="Команда разработки")
        team_design = Team(name="Design", description="Команда дизайна")
        session.add_all([team_eng, team_design])
        await session.flush()

        # ── Manager ───────────────────────────────────────────
        manager = Employee(
            full_name="Волков Дмитрий",
            email="admin@burnoutdetector.com",
            position="Head of Engineering",
            password_hash=get_password_hash("admin123"),
            role=RoleEnum.manager,
            team_id=team_eng.id,
            analysis_allowed=True,
        )
        session.add(manager)
        await session.flush()

        # Manager settings
        mgr_settings = ManagerSetting(
            manager_id=manager.id,
            threshold_value=0.4,
            notification_period=NotificationPeriodEnum.daily,
            auto_motivation_enabled=True,
        )
        session.add(mgr_settings)

        # ── Employees ─────────────────────────────────────────
        employees: dict[str, Employee] = {}
        for email, profile in EMPLOYEE_PROFILES.items():
            emp = Employee(
                full_name=profile["name"],
                email=email,
                position=profile["position"],
                password_hash=get_password_hash("staff123"),
                role=RoleEnum.employee,
                team_id=team_eng.id,
                analysis_allowed=True,
            )
            session.add(emp)
            employees[email] = emp

        await session.flush()
        print(f"Created {len(employees)} employees + 1 manager.")

        # ── Motivation content ────────────────────────────────
        for text in MOTIVATION_QUOTES:
            session.add(MotivationContent(
                type=MotivationTypeEnum.quote,
                content=text,
                tags=["мотивация", "цитата"],
                created_by=manager.id,
            ))
        for text in MOTIVATION_SUGGESTIONS:
            session.add(MotivationContent(
                type=MotivationTypeEnum.suggestion,
                content=text,
                tags=["совет", "здоровье"],
                created_by=manager.id,
            ))
        for text in MOTIVATION_MEMES:
            session.add(MotivationContent(
                type=MotivationTypeEnum.meme,
                content=text,
                tags=["мем", "юмор"],
                created_by=manager.id,
            ))
        print("Motivation content added.")

        # ── Generate 30 days of data per employee ─────────────
        today = date.today()
        total_days = 30
        total_activities = 0
        total_states = 0
        total_notifications = 0

        for email, emp in employees.items():
            profile = EMPLOYEE_PROFILES[email]

            for day_offset in range(total_days):
                current_date = today - timedelta(days=total_days - 1 - day_offset)
                mood = _mood_for_day(profile, day_offset, total_days)
                pos, neu, neg, emotion = _sentiment_from_mood(mood)

                # ── Sentiment ──
                sentiment = Sentiment(
                    positive_ratio=pos,
                    neutral_ratio=neu,
                    negative_ratio=neg,
                    emotion=emotion,
                )
                session.add(sentiment)
                await session.flush()

                # ── Employee State ──
                summary = _analysis_for_mood(mood)
                state = EmployeeState(
                    employee_id=emp.id,
                    mood_index=mood,
                    sentiment_id=sentiment.id,
                    date=current_date,
                    analysis_summary=summary,
                )
                session.add(state)
                total_states += 1

                # ── Activities for this day ──

                # Messages (3-8 per day, weighted by mood)
                msg_count = random.randint(3, 8)
                messages = _pick_messages(mood, msg_count)
                for msg_text in messages:
                    hour = random.randint(9, 18)
                    minute = random.randint(0, 59)
                    dt = datetime(
                        current_date.year, current_date.month, current_date.day,
                        hour, minute, 0,
                    )
                    au = ActivityUnit(
                        employee_id=emp.id,
                        type=ActivityTypeEnum.message,
                        source="telegram",
                        datetime=dt,
                    )
                    session.add(au)
                    await session.flush()
                    session.add(Message(activity_id=au.id, text=msg_text))
                    total_activities += 1

                # Commits (1-4 per day)
                commit_count = random.randint(1, 4)
                for _ in range(commit_count):
                    idx = random.randint(0, len(COMMIT_TITLES) - 1)
                    hour = random.randint(10, 19)
                    dt = datetime(
                        current_date.year, current_date.month, current_date.day,
                        hour, random.randint(0, 59), 0,
                    )
                    au = ActivityUnit(
                        employee_id=emp.id,
                        type=ActivityTypeEnum.commit,
                        source="github",
                        datetime=dt,
                    )
                    session.add(au)
                    await session.flush()
                    session.add(Commit(
                        activity_id=au.id,
                        title=COMMIT_TITLES[idx],
                        description=COMMIT_DESCRIPTIONS[idx] or None,
                        lines_added=random.randint(5, 250),
                        lines_deleted=random.randint(0, 80),
                    ))
                    total_activities += 1

                # PR Comments (0-3 per day)
                comment_count = random.randint(0, 3)
                for _ in range(comment_count):
                    hour = random.randint(10, 18)
                    dt = datetime(
                        current_date.year, current_date.month, current_date.day,
                        hour, random.randint(0, 59), 0,
                    )
                    au = ActivityUnit(
                        employee_id=emp.id,
                        type=ActivityTypeEnum.comment,
                        source="github",
                        datetime=dt,
                    )
                    session.add(au)
                    await session.flush()
                    session.add(Comment(
                        activity_id=au.id,
                        text=random.choice(PR_COMMENTS),
                    ))
                    total_activities += 1

                # Events (1-3 per day)
                event_count = random.randint(1, 3)
                chosen_events = random.sample(EVENT_NAMES, min(event_count, len(EVENT_NAMES)))
                for ev_name, ev_desc, ev_dur in chosen_events:
                    hour = random.choice([9, 10, 11, 13, 14, 15, 16])
                    dt = datetime(
                        current_date.year, current_date.month, current_date.day,
                        hour, random.choice([0, 15, 30]), 0,
                    )
                    au = ActivityUnit(
                        employee_id=emp.id,
                        type=ActivityTypeEnum.event,
                        source="google_calendar",
                        datetime=dt,
                    )
                    session.add(au)
                    await session.flush()
                    session.add(Event(
                        activity_id=au.id,
                        name=ev_name,
                        text=ev_desc,
                        duration_hours=ev_dur,
                    ))
                    total_activities += 1

                # ── Notifications when mood < threshold ──
                if mood < 0.4:
                    notif = Notification(
                        manager_id=manager.id,
                        employee_id=emp.id,
                        type=NotificationTypeEnum.alert,
                        title="Низкий индекс настроения",
                        content=f"Индекс настроения сотрудника {emp.full_name} снизился до {mood}. {summary}",
                        is_read=random.choice([True, False]),
                    )
                    session.add(notif)
                    total_notifications += 1

                    # Motivation sent notification
                    if random.random() < 0.7:
                        motiv_notif = Notification(
                            manager_id=manager.id,
                            employee_id=emp.id,
                            type=NotificationTypeEnum.motivation_sent,
                            title="Мотивация отправлена",
                            content=f"Сотруднику {emp.full_name} отправлена мотивационная цитата.",
                            is_read=random.choice([True, True, False]),
                        )
                        session.add(motiv_notif)
                        total_notifications += 1

            print(f"  {email}: 30 days of data generated (mood trend: {profile['trend']})")

        # ── Weekly report notifications ───────────────────────
        for week in range(4):
            report_date = today - timedelta(days=week * 7)
            report_notif = Notification(
                manager_id=manager.id,
                employee_id=list(employees.values())[0].id,
                type=NotificationTypeEnum.report,
                title=f"Еженедельный отчёт за {report_date.strftime('%d.%m.%Y')}",
                content=f"Средний mood index команды Engineering: {random.uniform(0.50, 0.75):.2f}. "
                        f"Сотрудников с низким настроением: {random.randint(0, 2)}. "
                        f"Подробности доступны в дашборде.",
                is_read=week > 0,
            )
            session.add(report_notif)
            total_notifications += 1

        await session.commit()

        print()
        print("=" * 55)
        print("  Database seeded successfully!")
        print("=" * 55)
        print(f"  Teams:          2")
        print(f"  Employees:      {len(employees)} + 1 manager")
        print(f"  Activities:     {total_activities}")
        print(f"  Employee states:{total_states}")
        print(f"  Notifications:  {total_notifications}")
        print(f"  Motivation:     {len(MOTIVATION_QUOTES) + len(MOTIVATION_SUGGESTIONS) + len(MOTIVATION_MEMES)}")
        print()
        print("  Test accounts:")
        print("  Manager:  admin@burnoutdetector.com / admin123")
        print("  Employee: employee@burnoutdetector.com / staff123")
        print("  Employee: ivanov@company.com / staff123")
        print("  Employee: petrova@company.com / staff123")
        print("  Employee: sidorov@company.com / staff123")
        print()
        print("  Employee mood profiles:")
        print("  Иванов Иван    — stable (0.72 base)")
        print("  Петрова Мария   — improving (0.80 base, trending up)")
        print("  Сидоров Алексей — declining (0.55 base, trending down)")
        print("  Козлова Елена   — wave (0.65 base, oscillating)")


if __name__ == "__main__":
    asyncio.run(seed())
