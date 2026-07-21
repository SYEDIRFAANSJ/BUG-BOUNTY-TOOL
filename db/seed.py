import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from shared.database import SessionLocal, engine, Base
from db.models import Platform

async def seed_data():
    async with engine.begin() as conn:
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # Check if platforms exist
        result = await session.execute(select(Platform))
        existing_platforms = result.scalars().all()
        
        if not existing_platforms:
            platforms = [
                Platform(name="HackerOne", api_base_url="https://api.hackerone.com/v1", rate_limit_per_min=50),
                Platform(name="Bugcrowd", api_base_url="https://api.bugcrowd.com", rate_limit_per_min=60),
                Platform(name="Intigriti", api_base_url="https://api.intigriti.com/external/researcher", rate_limit_per_min=30),
            ]
            
            for p in platforms:
                session.add(p)
                
            await session.commit()
            print("Database seeded with platforms.")
        else:
            print("Platforms already exist in the database. Skipping seed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
