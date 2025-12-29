"""
Service Model - Represents backend services
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ServiceBase(SQLModel):
    """Base service fields"""
    name: str = Field(index=True, unique=True)
    display_name: str
    description: Optional[str] = None
    base_url: str
    is_active: bool = Field(default=True)


class Service(ServiceBase, table=True):
    """Service database model"""
    __tablename__ = "services"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceCreate(SQLModel):
    """Schema for creating a service"""
    name: str
    display_name: str
    description: Optional[str] = None
    base_url: str = "https://jsonplaceholder.typicode.com"
