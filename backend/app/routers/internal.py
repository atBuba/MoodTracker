import os
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.utils.pagination import success_response
from app.utils.exceptions import AppException
from app.schemas.internal import ActivityCreateInternal, EmployeeStateInternal, SentimentInternal

from app.models.employee import Employee
from app.models.activity import ActivityUnit, Message, Commit, Comment, Event
from app.models.employee_state import EmployeeState
from app.models.sentiment import Sentiment

router = APIRouter(prefix="/api/internal", tags=["Internal"])

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "your-internal-api-key")

def verify_internal_api_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != INTERNAL_API_KEY:
        raise AppException(status_code=403, code="FORBIDDEN", message="Invalid Internal API Key")
    return True

@router.post("/activity", dependencies=[Depends(verify_internal_api_key)])
async def save_activity(payload: ActivityCreateInternal, db: AsyncSession = Depends(get_db)):
    # Find Employee by email 
    result = await db.execute(select(Employee).where(Employee.email == payload.employee_email))
    employee = result.scalars().first()
    
    if not employee:
        raise AppException(status_code=404, code="NOT_FOUND", message=f"Employee with email {payload.employee_email} not found")

    #  ActivityUnit 
    activity_unit = ActivityUnit(
        employee_id=employee.id,
        type=payload.type,
        source=payload.source,
        datetime=payload.datetime
    )
    db.add(activity_unit)
    await db.flush() 

    data = payload.data
    if payload.type == "message":
        detail = Message(activity_id=activity_unit.id, text=data.get("text", ""))
    elif payload.type == "commit":
        detail = Commit(
            activity_id=activity_unit.id,
            title=data.get("title", "No title"),
            description=data.get("description"),
            lines_added=data.get("lines_added", 0),
            lines_deleted=data.get("lines_deleted", 0)
        )
    elif payload.type == "comment":
        detail = Comment(activity_id=activity_unit.id, text=data.get("text", ""))
    elif payload.type == "event":
        detail = Event(
            activity_id=activity_unit.id,
            name=data.get("name", "Unnamed Event"),
            text=data.get("text"),
            duration_hours=data.get("duration_hours")
        )
    else:
        raise AppException(status_code=400, code="BAD_REQUEST", message="Invalid activity type")

    db.add(detail)
    await db.commit()

    return success_response({"message": "Activity saved successfully", "activity_id": str(activity_unit.id)})

@router.post("/employee-state", dependencies=[Depends(verify_internal_api_key)])
async def save_employee_state(payload: EmployeeStateInternal, db: AsyncSession = Depends(get_db)):
    sentiment_id = None
    
    if payload.sentiment_data:
        sentiment = Sentiment(
            positive_ratio=payload.sentiment_data.get("positive_ratio", 0.0),
            neutral_ratio=payload.sentiment_data.get("neutral_ratio", 0.0),
            negative_ratio=payload.sentiment_data.get("negative_ratio", 0.0),
            emotion=payload.sentiment_data.get("emotion")
        )
        db.add(sentiment)
        await db.flush() 
        sentiment_id = sentiment.id

    result = await db.execute(
        select(EmployeeState).where(
            EmployeeState.employee_id == payload.employee_id,
            EmployeeState.date == payload.date
        )
    )
    existing_state = result.scalars().first()

    if existing_state:
        existing_state.mood_index = payload.mood_index
        existing_state.analysis_summary = payload.analysis_summary
        if sentiment_id:
            existing_state.sentiment_id = sentiment_id
    else:
        new_state = EmployeeState(
            employee_id=payload.employee_id,
            mood_index=payload.mood_index,
            sentiment_id=sentiment_id,
            date=payload.date,
            analysis_summary=payload.analysis_summary
        )
        db.add(new_state)

    await db.commit()
    return success_response({"message": "State saved successfully"})

@router.post("/sentiment", dependencies=[Depends(verify_internal_api_key)])
async def save_sentiment(payload: SentimentInternal, db: AsyncSession = Depends(get_db)):
    new_sentiment = Sentiment(
        positive_ratio=payload.positive_ratio,
        neutral_ratio=payload.neutral_ratio,
        negative_ratio=payload.negative_ratio,
        emotion=payload.emotion
    )
    db.add(new_sentiment)
    await db.commit()
    await db.refresh(new_sentiment) 
    
    return success_response({"id": str(new_sentiment.id)})