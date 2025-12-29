"""
Partner-Service Permission Model - Junction table for many-to-many relationship
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class PartnerServicePermission(SQLModel, table=True):
    """Partner-Service permission junction table"""
    __tablename__ = "partner_service_permissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    partner_id: int = Field(foreign_key="partners.id", index=True)
    service_id: int = Field(foreign_key="services.id", index=True)
    granted_at: datetime = Field(default_factory=datetime.utcnow)
