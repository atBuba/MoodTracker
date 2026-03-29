from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Emotion(str, Enum):
    JOY = "joy"
    ANGER = "anger"
    SADNESS = "sadness"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


class TextItem(BaseModel):
    id: str
    text: str


class SentimentRequest(BaseModel):
    texts: list[TextItem]


class SentimentResult(BaseModel):
    id: str
    positive_ratio: float = Field(ge=0.0, le=1.0)
    neutral_ratio: float = Field(ge=0.0, le=1.0)
    negative_ratio: float = Field(ge=0.0, le=1.0)
    emotion: Emotion


class SentimentResponse(BaseModel):
    data: list[SentimentResult]
