from __future__ import annotations
import uuid
import enum
import datetime as dt
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class RoleEnum(str, enum.Enum):
    employee = 'employee'
    manager = 'manager'
    admin = 'admin'

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("teams.id"), nullable=True)
    analysis_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="employees")
    manager_settings: Mapped[Optional["ManagerSetting"]] = relationship("ManagerSetting", back_populates="manager")