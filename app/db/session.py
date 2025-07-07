import asyncio

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def wait_for_db():
    retries = 5
    while retries:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                print("✅ Database is ready!")
                return
        except OperationalError:
            print("⏳ Waiting for database...")
            await asyncio.sleep(3)
            retries -= 1
    print("❌ Database connection failed!")
    raise RuntimeError("Database is not available")
