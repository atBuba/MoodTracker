from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, 
    employees, 
    teams, 
    dashboard, 
    notifications, 
    settings, 
    content, 
    internal
)
from app.utils.exceptions import AppException, app_exception_handler

app = FastAPI(
    title="BurnOutDetector API",
    description="Backend Service for BurnOutDetector (FastAPI + Celery + PostgreSQL)",
    version="1.0.0",
    docs_url="/docs", 
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom error: {"error": {"code": "...", "message": "..."}}
app.add_exception_handler(AppException, app_exception_handler)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(teams.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(settings.router)
app.include_router(content.router)
app.include_router(internal.router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "burnoutdetector-backend"}