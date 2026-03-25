import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models import Employee, Team 
from app.services.auth_service import get_password_hash

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://moodtracker:changeme@localhost:5432/moodtracker")

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        from sqlalchemy import select
        existing = await session.execute(select(Employee).limit(1))
        if existing.scalars().first():
            return
        # Team
        team = Team(name="Engineering", description="Dev team")
        session.add(team)
        await session.flush()

        # Manager Account
        manager = Employee(
            full_name="Admin Manager",
            email="admin@moodtracker.com",
            position="Head of Engineering",
            password_hash=get_password_hash("admin123"),
            role="manager",
            team_id=team.id
        )
        session.add(manager)
        
        # Employee
        staff = Employee(
            full_name="Employee 1",
            email="employee@moodtracker.com",
            position="Software Engineer",
            password_hash=get_password_hash("staff123"),
            role="employee",
            team_id=team.id
        )
        session.add(staff)

        await session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())