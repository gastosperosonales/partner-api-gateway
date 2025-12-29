"""
Rate Limit Tracking Model
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class RateLimitEntry(SQLModel, table=True):
    """Tracks request timestamps for rate limiting"""
    __tablename__ = "rate_limit_entries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    partner_id: int = Field(foreign_key="partners.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
