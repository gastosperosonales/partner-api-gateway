"""
Rate Limiter Service - Database-backed sliding window rate limiting
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
from app.models.rate_limit import RateLimitEntry
from app.config import get_settings

settings = get_settings()


class RateLimiterService:
    """Service for rate limiting partners"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.window_seconds = settings.rate_limit_window
    
    async def _cleanup_old_entries(self, partner_id: int, cutoff: datetime):
        """Remove entries outside the current window"""
        statement = delete(RateLimitEntry).where(
            RateLimitEntry.partner_id == partner_id,
            RateLimitEntry.timestamp < cutoff
        )
        await self.session.execute(statement)
        await self.session.commit()
    
    async def _count_requests(self, partner_id: int, cutoff: datetime) -> int:
        """Count requests within the current window"""
        statement = select(RateLimitEntry).where(
            RateLimitEntry.partner_id == partner_id,
            RateLimitEntry.timestamp >= cutoff
        )
        result = await self.session.execute(statement)
        results = result.scalars().all()
        return len(results)
    
    async def _record_request(self, partner_id: int):
        """Record a new request"""
        entry = RateLimitEntry(partner_id=partner_id)
        self.session.add(entry)
        await self.session.commit()
    
    async def check_rate_limit(self, partner_id: int, limit: int) -> Tuple[bool, Dict]:
        """
        Check if partner is within rate limit
        
        Returns:
            (allowed: bool, info: dict with remaining, reset_at, etc.)
        """
        current_time = datetime.utcnow()
        cutoff = current_time - timedelta(seconds=self.window_seconds)
        
        # Clean up old entries
        await self._cleanup_old_entries(partner_id, cutoff)
        
        # Count current requests
        request_count = await self._count_requests(partner_id, cutoff)
        remaining = max(0, limit - request_count)
        reset_at = int((current_time + timedelta(seconds=self.window_seconds)).timestamp())
        
        info = {
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at,
            "window_seconds": self.window_seconds,
            "used": request_count
        }
        
        if request_count >= limit:
            return False, info
        
        # Record this request
        await self._record_request(partner_id)
        info["remaining"] = remaining - 1
        info["used"] = request_count + 1
        
        return True, info
    
    async def get_usage(self, partner_id: int, limit: int) -> Dict:
        """Get current usage stats for a partner"""
        current_time = datetime.utcnow()
        cutoff = current_time - timedelta(seconds=self.window_seconds)
        
        request_count = await self._count_requests(partner_id, cutoff)
        
        return {
            "used": request_count,
            "limit": limit,
            "remaining": max(0, limit - request_count),
            "window_seconds": self.window_seconds
        }
    
    async def reset(self, partner_id: int):
        """Reset rate limit for a partner"""
        statement = delete(RateLimitEntry).where(
            RateLimitEntry.partner_id == partner_id
        )
        await self.session.execute(statement)
        await self.session.commit()
