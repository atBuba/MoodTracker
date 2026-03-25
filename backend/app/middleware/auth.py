from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db
from app.models.employee import Employee
from app.services.auth_service import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

redis_client = redis.from_url("redis://redis:6379/0", decode_responses=True)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}, 
    )
    
    # Check Blacklist in Redis 
    is_blacklisted = await redis_client.get(f"bl_{token}")
    if is_blacklisted:
        raise HTTPException(status_code=401, detail="Token revoked")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("employee_id")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(Employee, user_id)
    if not user:
        raise credentials_exception
        
    return user

def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: Employee = Depends(get_current_user)):
        if current_user.role.value not in allowed_roles: 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You don't have enough permissions."
            )
        return current_user
    return role_checker