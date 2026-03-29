from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    MESSAGE = "message"
    COMMIT = "commit"
    COMMENT = "comment"
    EVENT = "event"


class ActivitySource(str, Enum):
    TELEGRAM = "telegram"
    GITHUB = "github"
    GOOGLE_CALENDAR = "google_calendar"


class MessageData(BaseModel):
    text: str


class CommitData(BaseModel):
    title: str
    description: str = ""
    lines_added: int = 0
    lines_deleted: int = 0


class CommentData(BaseModel):
    text: str


class EventData(BaseModel):
    name: str
    text: str = ""
    duration_hours: float = 0.0


class ActivityUnit(BaseModel):
    employee_email: str
    type: ActivityType
    source: ActivitySource
    datetime: datetime
    data: dict[str, Any]

    def to_request_dict(self) -> dict[str, Any]:
        return {
            "employee_email": self.employee_email,
            "type": self.type.value,
            "source": self.source.value,
            "datetime": self.datetime.isoformat(),
            "data": self.data,
        }
