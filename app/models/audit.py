"""
Request Log Model - Tracks all API requests
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class RequestLogBase(SQLModel):
    """Base request log fields"""
    partner_id: int = Field(foreign_key="partners.id", index=True)
    method: str
    path: str = Field(index=True)
    status_code: int
    response_time_ms: float
    ip_address: str
    user_agent: Optional[str] = None


class RequestLog(RequestLogBase, table=True):
    """Request log database model"""
    __tablename__ = "request_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


class RequestLogCreate(RequestLogBase):
    """Schema for creating a request log"""
    pass


class RequestLogRead(RequestLogBase):
    """Schema for reading a request log"""
    id: int
    timestamp: datetime
