from __future__ import annotations
import uuid
import enum
import datetime as dt

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class NotificationTypeEnum(str, enum.Enum):
    report = 'report'
    alert = 'alert'
    motivation_sent = 'motivation_sent'

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), nullable=False)
    type: Mapped[NotificationTypeEnum] = mapped_column(Enum(NotificationTypeEnum), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())