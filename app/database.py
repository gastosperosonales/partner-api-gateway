"""
Database Configuration
SQLModel with SQLite (Async)
"""
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import get_settings

settings = get_settings()

# Convert sqlite:/// to sqlite+aiosqlite:///
async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# Create async engine with SQLite
engine = create_async_engine(
    async_database_url,
    echo=False,  # Set to True for SQL query logging
    connect_args={"check_same_thread": False},  # Needed for SQLite
    poolclass=StaticPool  # Use StaticPool for SQLite
)

# Create async session maker
Async_Session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def create_db_and_tables() -> None:
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions"""
    async with Async_Session() as session:
        yield session
