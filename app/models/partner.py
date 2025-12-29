"""
Partner Model - Represents API partners/clients
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field
import hashlib
import secrets


class PartnerBase(SQLModel):
    """Base partner fields"""
    name: str = Field(index=True)
    rate_limit: int = Field(default=60)
    is_active: bool = Field(default=True)


class Partner(PartnerBase, table=True):
    """Partner database model"""
    __tablename__ = "partners"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    api_key_hash: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Cached allowed services - populated at runtime
    _allowed_services: List[str] = []
    
    @property
    def allowed_services(self) -> List[str]:
        """Get list of allowed services (should be populated by service layer)"""
        return self._allowed_services
    
    @allowed_services.setter
    def allowed_services(self, services: List[str]) -> None:
        """Set allowed services"""
        self._allowed_services = services
    
    def can_access_service(self, service_name: str) -> bool:
        """Check if partner can access a specific service"""
        return service_name in self._allowed_services
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key"""
        return f"ak_{secrets.token_urlsafe(32)}"
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify if provided API key matches"""
        return self.hash_api_key(api_key) == self.api_key_hash


class PartnerCreate(SQLModel):
    """Schema for creating a partner"""
    name: str
    rate_limit: int = 60
    service_ids: List[int] = Field(default_factory=list)  # Services to grant access to


class PartnerRead(PartnerBase):
    """Schema for reading a partner (public data)"""
    id: int
    allowed_services: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PartnerReadWithKey(PartnerRead):
    """Schema for reading a partner with API key (only shown once)"""
    api_key: str


class PartnerUpdate(SQLModel):
    """Schema for updating a partner"""
    name: Optional[str] = None
    allowed_services: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None


class PartnerWithServices(PartnerRead):
    """Schema for reading a partner with their allowed services"""
    services: List[str] = Field(default_factory=list)