"""
Health & Info Routes - Public endpoints (no auth required)
"""
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/")
def index():
    """Gateway info endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "available_services": ["users", "posts", "comments", "todos", "albums", "photos"]
    }


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
