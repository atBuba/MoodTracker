import pytest
from datetime import datetime, timezone

from app.collectors.mock import MockCollector, MOCK_EMPLOYEES
from app.schemas.activity import ActivityType, ActivitySource


@pytest.mark.asyncio
async def test_mock_collector_generates_activities():
    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))

    assert len(activities) > 0
    # At minimum: 2 messages + 1 commit + 1 event per employee = 4 * 3 = 12
    assert len(activities) >= 12


@pytest.mark.asyncio
async def test_mock_collector_covers_all_types():
    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))

    types = {a.type for a in activities}
    assert ActivityType.MESSAGE in types
    assert ActivityType.COMMIT in types
    assert ActivityType.EVENT in types


@pytest.mark.asyncio
async def test_mock_collector_covers_all_sources():
    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))

    sources = {a.source for a in activities}
    assert ActivitySource.TELEGRAM in sources
    assert ActivitySource.GITHUB in sources
    assert ActivitySource.GOOGLE_CALENDAR in sources


@pytest.mark.asyncio
async def test_mock_collector_uses_known_emails():
    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))

    emails = {a.employee_email for a in activities}
    for email in emails:
        assert email in MOCK_EMPLOYEES


@pytest.mark.asyncio
async def test_mock_collector_activity_serialization():
    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))

    for activity in activities:
        d = activity.to_request_dict()
        assert "employee_email" in d
        assert "type" in d
        assert "source" in d
        assert "datetime" in d
        assert "data" in d
        assert d["type"] in ("message", "commit", "comment", "event")


@pytest.mark.asyncio
async def test_mock_collector_commit_data_has_required_fields():
    collector = MockCollector()
    activities = await collector.collect(since=datetime.now(timezone.utc))

    commits = [a for a in activities if a.type == ActivityType.COMMIT]
    assert len(commits) > 0

    for commit in commits:
        assert "title" in commit.data
        assert "lines_added" in commit.data
        assert "lines_deleted" in commit.data
