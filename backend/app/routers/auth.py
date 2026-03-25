import time
import os
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError

from app.database import get_db
from app.models.employee import Employee
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import verify_password, create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM
from app.middleware.auth import get_current_user, redis_client, oauth2_scheme
from app.utils.exceptions import AppException  
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise AppException(status_code=401, code="INVALID_CREDENTIALS", message="Incorrect email or password")

    access_token = create_access_token(
        data={"employee_id": str(user.id)} 
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    is_blacklisted = await redis_client.get(f"bl_{refresh_token}")
    if is_blacklisted:
        raise HTTPException(status_code=401, detail="Token revoked")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        user_id = payload.get("employee_id")
        user = await db.get(Employee, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        new_access = create_access_token({
            "employee_id": str(user.id),
            "role": user.role.value,
            "team_id": str(user.team_id) if user.team_id else None
        })
        return TokenResponse(access_token=new_access, token_type="bearer")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
async def logout(
    request: Request, 
    response: Response, 
    access_token: str = Depends(oauth2_scheme) 
):
    # Take Refresh Token into Blacklist
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            ttl = int(payload.get("exp") - time.time())
            if ttl > 0:
                await redis_client.setex(f"bl_{refresh_token}", ttl, "revoked")
        except JWTError:
            pass
            
    # Take Access Token into Blacklist (Kick user immediately)
    if access_token:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            ttl = int(payload.get("exp") - time.time())
            if ttl > 0:
                await redis_client.setex(f"bl_{access_token}", ttl, "revoked")
        except JWTError:
            pass

    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Employee = Depends(get_current_user)):
    return current_user