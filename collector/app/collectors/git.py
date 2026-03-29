import logging
from datetime import datetime, timezone

import httpx
import redis.asyncio as aioredis

from app.collectors.base import BaseCollector
from app.config import settings
from app.schemas.activity import (
    ActivitySource,
    ActivityType,
    ActivityUnit,
    CommentData,
    CommitData,
)

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
REDIS_KEY_PREFIX = "collector:git:last_check"


class GitCollector(BaseCollector):
    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return self._redis

    async def _get_last_check(self, repo: str, kind: str) -> datetime:
        r = await self._get_redis()
        key = f"{REDIS_KEY_PREFIX}:{repo}:{kind}"
        val = await r.get(key)
        if val:
            return datetime.fromisoformat(val)
        # Default: 1 hour ago
        return datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )

    async def _set_last_check(self, repo: str, kind: str, dt: datetime) -> None:
        r = await self._get_redis()
        key = f"{REDIS_KEY_PREFIX}:{repo}:{kind}"
        await r.set(key, dt.isoformat())

    async def _handle_rate_limit(self, response: httpx.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) < 10:
            reset_ts = response.headers.get("X-RateLimit-Reset")
            if reset_ts:
                reset_dt = datetime.fromtimestamp(int(reset_ts), tz=timezone.utc)
                logger.warning(
                    "GitHub rate limit low (%s remaining), resets at %s",
                    remaining,
                    reset_dt.isoformat(),
                )

    async def _fetch_commits(self, repo: str, since: datetime) -> list[ActivityUnit]:
        activities: list[ActivityUnit] = []
        url = f"{GITHUB_API_BASE}/repos/{repo}/commits"
        params = {"since": since.isoformat(), "per_page": 100}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers, params=params)
            await self._handle_rate_limit(response)
            response.raise_for_status()
            commits = response.json()

        for commit_data in commits:
            commit_info = commit_data.get("commit", {})
            author = commit_info.get("author", {})
            email = author.get("email", "")
            if not email:
                continue

            message_lines = commit_info.get("message", "").split("\n", 1)
            title = message_lines[0]
            description = message_lines[1].strip() if len(message_lines) > 1 else ""

            commit_date_str = author.get("date", "")
            try:
                commit_dt = datetime.fromisoformat(
                    commit_date_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                commit_dt = datetime.now(timezone.utc)

            stats = commit_data.get("stats", {})
            lines_added = stats.get("additions", 0)
            lines_deleted = stats.get("deletions", 0)

            activity = ActivityUnit(
                employee_email=email,
                type=ActivityType.COMMIT,
                source=ActivitySource.GITHUB,
                datetime=commit_dt,
                data=CommitData(
                    title=title,
                    description=description,
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                ).model_dump(),
            )
            activities.append(activity)

        return activities

    async def _fetch_pr_comments(
        self, repo: str, since: datetime
    ) -> list[ActivityUnit]:
        activities: list[ActivityUnit] = []
        url = f"{GITHUB_API_BASE}/repos/{repo}/pulls/comments"
        params = {"since": since.isoformat(), "per_page": 100, "sort": "updated"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers, params=params)
            await self._handle_rate_limit(response)
            response.raise_for_status()
            comments = response.json()

        for comment in comments:
            user = comment.get("user", {})
            # GitHub API does not expose email in comment payload directly;
            # we use the commit author association or login as fallback.
            email = user.get("email") or f"{user.get('login', 'unknown')}@github"
            body = comment.get("body", "")
            created_str = comment.get("created_at", "")

            try:
                created_dt = datetime.fromisoformat(
                    created_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                created_dt = datetime.now(timezone.utc)

            activity = ActivityUnit(
                employee_email=email,
                type=ActivityType.COMMENT,
                source=ActivitySource.GITHUB,
                datetime=created_dt,
                data=CommentData(text=body).model_dump(),
            )
            activities.append(activity)

        return activities

    async def collect(self, since: datetime) -> list[ActivityUnit]:
        all_activities: list[ActivityUnit] = []

        for repo in settings.github_repos_list:
            try:
                commit_since = await self._get_last_check(repo, "commits")
                commits = await self._fetch_commits(repo, commit_since)
                all_activities.extend(commits)
                if commits:
                    latest = max(a.datetime for a in commits)
                    await self._set_last_check(repo, "commits", latest)
                logger.info("Collected %d commits from %s", len(commits), repo)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.error("GitHub rate limit hit for %s commits", repo)
                else:
                    logger.exception("Failed to fetch commits from %s", repo)
            except Exception:
                logger.exception("Failed to fetch commits from %s", repo)

            try:
                comment_since = await self._get_last_check(repo, "comments")
                comments = await self._fetch_pr_comments(repo, comment_since)
                all_activities.extend(comments)
                if comments:
                    latest = max(a.datetime for a in comments)
                    await self._set_last_check(repo, "comments", latest)
                logger.info("Collected %d PR comments from %s", len(comments), repo)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.error("GitHub rate limit hit for %s comments", repo)
                else:
                    logger.exception("Failed to fetch PR comments from %s", repo)
            except Exception:
                logger.exception("Failed to fetch PR comments from %s", repo)

        return all_activities

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
