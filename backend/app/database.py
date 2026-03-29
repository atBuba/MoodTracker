import os
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/burnoutdetector"
)

class Base(AsyncAttrs, DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()