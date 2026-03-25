from __future__ import annotations
import uuid
import datetime as dt
from typing import List

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="team")