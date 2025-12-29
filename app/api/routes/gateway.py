"""
Gateway Routes - Proxy requests to backend services
"""
import time
from typing import Annotated
import httpx
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.partner import Partner
from app.models.audit import RequestLogCreate
from app.api.deps import get_authenticated_partner
from app.services.audit import RequestLoggerService
from app.config import get_settings

router = APIRouter(tags=["Gateway"])
settings = get_settings()


async def proxy_to_backend(
    request: Request,
    path: str,
    partner: Partner,
    session: AsyncSession
) -> Response:
    """Proxy a request to the backend service"""
    start_time = time.time()
    
    # Build backend URL
    backend_url = f"{settings.backend_base_url}/{path}"
    
    # Forward query parameters
    params = dict(request.query_params)
    
    # Forward headers (excluding auth headers)
    headers = {
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Accept": request.headers.get("Accept", "application/json")
    }
    
    # Get request body for POST/PUT/PATCH
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            backend_response = await client.request(
                method=request.method,
                url=backend_url,
                headers=headers,
                params=params,
                content=body
            )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log the request
        logger_service = RequestLoggerService(session)
        await logger_service.log_request(RequestLogCreate(
            partner_id=partner.id,
            method=request.method,
            path=f"/{path}",
            status_code=backend_response.status_code,
            response_time_ms=response_time_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent")
        ))
        
        # Build response with rate limit headers
        rate_info = request.state.rate_info
        response_headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset_at"]),
            "X-Gateway-Partner-Id": str(partner.id),
            "X-Backend-Response-Time": f"{int(backend_response.elapsed.total_seconds() * 1000)}ms"
        }
        
        return Response(
            content=backend_response.content,
            status_code=backend_response.status_code,
            headers=response_headers,
            media_type=backend_response.headers.get("Content-Type", "application/json")
        )
        
    except httpx.TimeoutException:
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log the timeout
        logger_service = RequestLoggerService(session)
        await logger_service.log_request(RequestLogCreate(
            partner_id=partner.id,
            method=request.method,
            path=f"/{path}",
            status_code=504,
            response_time_ms=response_time_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent")
        ))
        
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Gateway Timeout",
                "message": "Backend service did not respond in time"
            }
        )
        
    except httpx.RequestError as e:
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log the error
        logger_service = RequestLoggerService(session)
        await logger_service.log_request(RequestLogCreate(
            partner_id=partner.id,
            method=request.method,
            path=f"/{path}",
            status_code=502,
            response_time_ms=response_time_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent")
        ))
        
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Bad Gateway",
                "message": f"Error communicating with backend service: {str(e)}"
            }
        )


# =============================================================================
# Proxy Routes for Each Service
# =============================================================================

@router.get("/{path:path}")
async def proxy_get(
    request: Request,
    path: str,
    partner: Annotated[Partner, Depends(get_authenticated_partner)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """Proxy GET requests to backend"""
    return await proxy_to_backend(request, path, partner, session)


@router.post("/{path:path}")
async def proxy_post(
    request: Request,
    path: str,
    partner: Annotated[Partner, Depends(get_authenticated_partner)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """Proxy POST requests to backend"""
    return await proxy_to_backend(request, path, partner, session)


@router.put("/{path:path}")
async def proxy_put(
    request: Request,
    path: str,
    partner: Annotated[Partner, Depends(get_authenticated_partner)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """Proxy PUT requests to backend"""
    return await proxy_to_backend(request, path, partner, session)


@router.patch("/{path:path}")
async def proxy_patch(
    request: Request,
    path: str,
    partner: Annotated[Partner, Depends(get_authenticated_partner)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """Proxy PATCH requests to backend"""
    return await proxy_to_backend(request, path, partner, session)


@router.delete("/{path:path}")
async def proxy_delete(
    request: Request,
    path: str,
    partner: Annotated[Partner, Depends(get_authenticated_partner)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """Proxy DELETE requests to backend"""
    return await proxy_to_backend(request, path, partner, session)
