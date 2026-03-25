from __future__ import annotations
import uuid
import enum
import datetime as dt

from sqlalchemy import Float, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class NotificationPeriodEnum(str, enum.Enum):
    immediate = 'immediate'
    daily = 'daily'
    weekly = 'weekly'

class ManagerSetting(Base):
    __tablename__ = "manager_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), unique=True, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, default=0.4)
    notification_period: Mapped[NotificationPeriodEnum] = mapped_column(Enum(NotificationPeriodEnum), default=NotificationPeriodEnum.daily)
    auto_motivation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    manager: Mapped["Employee"] = relationship("Employee", back_populates="manager_settings")