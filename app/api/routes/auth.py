"""
Auth Routes - JWT token generation
"""
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
import jwt
from pydantic import BaseModel
from loguru import logger

from app.database import get_session
from app.services.partner import PartnerService
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


# =============================================================================
# Schemas
# =============================================================================

class TokenRequest(BaseModel):
    """Request schema for token generation"""
    api_key: str


class TokenResponse(BaseModel):
    """Response schema for token generation"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    partner_id: int
    partner_name: str
    allowed_services: list[str]
    rate_limit: int


# =============================================================================
# JWT Utilities
# =============================================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


# =============================================================================
# Routes
# =============================================================================

@router.post("/token", response_model=TokenResponse)
async def get_token(
    token_request: TokenRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Exchange API key for JWT access token.
    
    The JWT token contains partner metadata and should be used for all 
    subsequent API requests via the Authorization: Bearer <token> header.
    """
    # Validate API key and get partner
    partner_service = PartnerService(session)
    partner = await partner_service.get_partner_by_api_key(token_request.api_key)
    
    if not partner:
        logger.warning("Token request failed: invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Invalid API key"
            }
        )
    
    if not partner.is_active:
        logger.warning("Token request failed: partner deactivated id={}", partner.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "API key has been deactivated"
            }
        )
    
    # Create JWT token with partner metadata
    token_data = {
        "sub": str(partner.id),  # subject (partner ID)
        "partner_id": partner.id,
        "partner_name": partner.name,
        "allowed_services": partner.allowed_services,
        "rate_limit": partner.rate_limit,
        "is_active": partner.is_active
    }
    
    access_token = create_access_token(token_data)
    logger.info("Access token issued: partner_id={} services={} rate_limit={}", partner.id, len(partner.allowed_services), partner.rate_limit)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        partner_id=partner.id,
        partner_name=partner.name,
        allowed_services=partner.allowed_services,
        rate_limit=partner.rate_limit
    )
