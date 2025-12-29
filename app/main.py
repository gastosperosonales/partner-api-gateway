"""
API Gateway - FastAPI Application
Main entry point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from loguru import logger

from app.config import get_settings
from app.database import create_db_and_tables
from app.api.routes import health, admin, gateway, auth
import app.models  # Import models to ensure they're registered with SQLModel

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown events"""
    # Startup
    await create_db_and_tables()
    logger.info("API Gateway started on {}:{}", settings.host, settings.port)
    yield
    
    # Shutdown
    logger.info("API Gateway shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API Gateway for managing external partner access to internal services",
    lifespan=lifespan,
)


# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(gateway.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
