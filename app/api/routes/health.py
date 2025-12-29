"""
Health & Info Routes - Public endpoints (no auth required)
"""
from typing import Dict, Any
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/")
def index() -> Dict[str, Any]:
    """Gateway info endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "available_services": ["users", "posts", "comments", "todos", "albums", "photos"]
    }


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}
