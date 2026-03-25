from __future__ import annotations
import uuid
import datetime as dt
from typing import Optional

from sqlalchemy import Float, Text, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class EmployeeState(Base):
    __tablename__ = "employee_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), nullable=False)
    mood_index: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sentiments.id"), nullable=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
    )