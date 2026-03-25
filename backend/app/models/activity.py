from __future__ import annotations
import uuid
import enum
import datetime as dt
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class ActivityTypeEnum(str, enum.Enum):
    message = 'message'
    commit = 'commit'
    comment = 'comment'
    event = 'event'

class ActivityUnit(Base):
    __tablename__ = "activity_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), nullable=False)
    type: Mapped[ActivityTypeEnum] = mapped_column(Enum(ActivityTypeEnum), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False) 
    datetime: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False) # Lỗi Pylance đã được fix ở đây
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_units.id"), unique=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

class Commit(Base):
    __tablename__ = "commits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_units.id"), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0)

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_units.id"), unique=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_units.id"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)