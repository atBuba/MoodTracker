import pytest
import httpx
import respx
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.collectors.git import GitCollector, GITHUB_API_BASE
from app.schemas.activity import ActivityType, ActivitySource


MOCK_COMMITS_RESPONSE = [
    {
        "sha": "abc123",
        "commit": {
            "author": {
                "name": "Ivan Ivanov",
                "email": "ivanov@company.com",
                "date": "2026-03-23T14:30:00Z",
            },
            "message": "feat: add user profile page\n\nImplemented the user profile with avatar support.",
        },
        "stats": {
            "additions": 150,
            "deletions": 20,
        },
    },
    {
        "sha": "def456",
        "commit": {
            "author": {
                "name": "Petra Petrova",
                "email": "petrova@company.com",
                "date": "2026-03-23T15:00:00Z",
            },
            "message": "fix: correct date formatting bug",
        },
        "stats": {
            "additions": 5,
            "deletions": 3,
        },
    },
]

MOCK_COMMENTS_RESPONSE = [
    {
        "id": 1,
        "body": "Looks good, but please add tests for the edge case.",
        "created_at": "2026-03-23T16:00:00Z",
        "user": {
            "login": "ivanov_dev",
            "email": "ivanov@company.com",
        },
    },
    {
        "id": 2,
        "body": "LGTM!",
        "created_at": "2026-03-23T16:30:00Z",
        "user": {
            "login": "reviewer_bot",
            "email": None,
        },
    },
]


@pytest.fixture
def git_collector():
    with patch.object(GitCollector, "__init__", lambda self: None):
        collector = GitCollector.__new__(GitCollector)
        collector._headers = {
            "Authorization": "Bearer test-token",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        collector._redis = None
        return collector


@pytest.mark.asyncio
async def test_fetch_commits_parses_correctly(git_collector):
    since = datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
    repo = "org/repo1"

    with respx.mock:
        respx.get(f"{GITHUB_API_BASE}/repos/{repo}/commits").mock(
            return_value=httpx.Response(
                200,
                json=MOCK_COMMITS_RESPONSE,
                headers={
                    "X-RateLimit-Remaining": "4999",
                    "X-RateLimit-Reset": "1711200000",
                },
            )
        )
        activities = await git_collector._fetch_commits(repo, since)

    assert len(activities) == 2

    first = activities[0]
    assert first.type == ActivityType.COMMIT
    assert first.source == ActivitySource.GITHUB
    assert first.employee_email == "ivanov@company.com"
    assert first.data["title"] == "feat: add user profile page"
    assert first.data["description"] == "Implemented the user profile with avatar support."
    assert first.data["lines_added"] == 150
    assert first.data["lines_deleted"] == 20

    second = activities[1]
    assert second.employee_email == "petrova@company.com"
    assert second.data["title"] == "fix: correct date formatting bug"
    assert second.data["description"] == ""
    assert second.data["lines_added"] == 5
    assert second.data["lines_deleted"] == 3


@pytest.mark.asyncio
async def test_fetch_commits_skips_no_email(git_collector):
    since = datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
    repo = "org/repo1"

    no_email_commit = [
        {
            "sha": "xyz789",
            "commit": {
                "author": {"name": "Bot", "email": "", "date": "2026-03-23T14:30:00Z"},
                "message": "automated commit",
            },
            "stats": {"additions": 1, "deletions": 0},
        }
    ]

    with respx.mock:
        respx.get(f"{GITHUB_API_BASE}/repos/{repo}/commits").mock(
            return_value=httpx.Response(200, json=no_email_commit)
        )
        activities = await git_collector._fetch_commits(repo, since)

    assert len(activities) == 0


@pytest.mark.asyncio
async def test_fetch_pr_comments_parses_correctly(git_collector):
    since = datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
    repo = "org/repo1"

    with respx.mock:
        respx.get(f"{GITHUB_API_BASE}/repos/{repo}/pulls/comments").mock(
            return_value=httpx.Response(200, json=MOCK_COMMENTS_RESPONSE)
        )
        activities = await git_collector._fetch_pr_comments(repo, since)

    assert len(activities) == 2

    first = activities[0]
    assert first.type == ActivityType.COMMENT
    assert first.source == ActivitySource.GITHUB
    assert first.employee_email == "ivanov@company.com"
    assert first.data["text"] == "Looks good, but please add tests for the edge case."

    # Second comment has no email, falls back to login@github
    second = activities[1]
    assert second.employee_email == "reviewer_bot@github"
    assert second.data["text"] == "LGTM!"


@pytest.mark.asyncio
async def test_fetch_commits_handles_rate_limit_403(git_collector):
    since = datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
    repo = "org/repo1"

    with respx.mock:
        respx.get(f"{GITHUB_API_BASE}/repos/{repo}/commits").mock(
            return_value=httpx.Response(403, json={"message": "API rate limit exceeded"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await git_collector._fetch_commits(repo, since)


@pytest.mark.asyncio
async def test_commit_to_request_dict():
    from app.schemas.activity import ActivityUnit, CommitData

    activity = ActivityUnit(
        employee_email="ivanov@company.com",
        type=ActivityType.COMMIT,
        source=ActivitySource.GITHUB,
        datetime=datetime(2026, 3, 23, 14, 30, tzinfo=timezone.utc),
        data=CommitData(
            title="feat: something",
            description="details",
            lines_added=10,
            lines_deleted=2,
        ).model_dump(),
    )
    d = activity.to_request_dict()
    assert d["type"] == "commit"
    assert d["source"] == "github"
    assert d["employee_email"] == "ivanov@company.com"
    assert d["data"]["lines_added"] == 10
