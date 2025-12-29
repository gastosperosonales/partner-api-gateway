"""
Admin Routes - Partner management and analytics
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.partner import PartnerCreate, PartnerReadWithKey
from app.services.partner import PartnerService
from app.services.audit import RequestLoggerService
from app.models.audit import RequestLogRead

router = APIRouter(prefix="/admin", tags=["Admin"])


# =============================================================================
# Partner Management
# =============================================================================

@router.get("/partners")
async def list_partners(
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """List all registered partners with their allowed services"""
    partner_service = PartnerService(session)
    return await partner_service.get_all_partners()


@router.post("/partners", response_model=PartnerReadWithKey)
async def create_partner(
    partner_data: PartnerCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Register a new partner with API key and permissions.
    Returns the API key - this is the only time it will be shown!
    """
    partner_service = PartnerService(session)
    partner, api_key = await partner_service.create_partner(partner_data)
    
    # Get allowed services
    allowed_services = await partner_service.get_partner_services(partner.id)
    
    return PartnerReadWithKey(
        id=partner.id,
        name=partner.name,
        allowed_services=allowed_services,
        rate_limit=partner.rate_limit,
        is_active=partner.is_active,
        created_at=partner.created_at,
        updated_at=partner.updated_at,
        api_key=api_key
    )


# =============================================================================
# Analytics & Logs
# =============================================================================

@router.get("/analytics")
async def get_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    hours: int = Query(24, ge=1, le=720)
):
    """Get API usage analytics for the past N hours"""
    logger_service = RequestLoggerService(session)
    return await logger_service.get_analytics(hours=hours)


@router.get("/logs", response_model=List[RequestLogRead])
async def get_logs(
    session: Annotated[AsyncSession, Depends(get_session)],
    partner_id: int | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get recent request logs"""
    logger_service = RequestLoggerService(session)
    return await logger_service.get_logs(
        partner_id=partner_id,
        limit=limit,
        offset=offset
    )
