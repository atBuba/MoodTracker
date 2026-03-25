from __future__ import annotations
import uuid
import enum
import datetime as dt
from typing import Optional, List

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base

class MotivationTypeEnum(str, enum.Enum):
    meme = 'meme'
    quote = 'quote'
    suggestion = 'suggestion'

class MotivationContent(Base):
    __tablename__ = "motivation_content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[MotivationTypeEnum] = mapped_column(Enum(MotivationTypeEnum), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("employees.id"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())