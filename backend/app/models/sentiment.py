import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class Sentiment(Base):
    __tablename__ = "sentiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    positive_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    neutral_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    negative_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    emotion: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())