import abc
import logging
from datetime import datetime

from app.schemas.activity import ActivityUnit
from app.services.backend_client import backend_client

logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    """Abstract base collector. Each concrete collector must implement collect()."""

    @abc.abstractmethod
    async def collect(self, since: datetime) -> list[ActivityUnit]:
        """Collect activities since the given timestamp."""
        ...

    async def send_to_backend(self, activities: list[ActivityUnit]) -> int:
        """Send collected activities to the backend. Returns the count of successfully sent items."""
        if not activities:
            return 0
        sent = await backend_client.send_activities(activities)
        logger.info(
            "%s: sent %d/%d activities to backend",
            self.__class__.__name__,
            sent,
            len(activities),
        )
        return sent
