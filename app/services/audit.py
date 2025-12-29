"""
Request Logger Service - Logs all API requests to database
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.models.audit import RequestLog, RequestLogCreate


class RequestLoggerService:
    """Service for logging and analyzing API requests"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_request(self, log_data: RequestLogCreate) -> RequestLog:
        """Log an API request"""
        log_entry = RequestLog(**log_data.model_dump())
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        return log_entry
    
    async def get_logs(
        self,
        partner_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RequestLog]:
        """Get request logs with optional filtering"""
        statement = select(RequestLog).order_by(RequestLog.timestamp.desc())
        
        if partner_id is not None:
            statement = statement.where(RequestLog.partner_id == partner_id)
        
        statement = statement.offset(offset).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
    
    async def get_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics summary for the past N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Total requests
        total_statement = select(func.count(RequestLog.id)).where(
            RequestLog.timestamp >= cutoff
        )
        total_result = await self.session.execute(total_statement)
        total_requests = total_result.scalar_one() or 0
        
        # Error count (status >= 400)
        error_statement = select(func.count(RequestLog.id)).where(
            RequestLog.timestamp >= cutoff,
            RequestLog.status_code >= 400
        )
        error_result = await self.session.execute(error_statement)
        total_errors = error_result.scalar_one() or 0
        
        # Average response time
        avg_statement = select(func.avg(RequestLog.response_time_ms)).where(
            RequestLog.timestamp >= cutoff
        )
        avg_result = await self.session.execute(avg_statement)
        avg_response_time = avg_result.scalar_one() or 0
        
        # Requests by partner
        partner_statement = select(
            RequestLog.partner_id,
            func.count(RequestLog.id).label("count")
        ).where(
            RequestLog.timestamp >= cutoff
        ).group_by(RequestLog.partner_id)
        
        partner_result = await self.session.execute(partner_statement)
        requests_by_partner = {
            row[0]: row[1] 
            for row in partner_result.all()
        }
        
        # Requests by endpoint (top 10)
        endpoint_statement = select(
            RequestLog.path,
            func.count(RequestLog.id).label("count")
        ).where(
            RequestLog.timestamp >= cutoff
        ).group_by(RequestLog.path).order_by(
            func.count(RequestLog.id).desc()
        ).limit(10)
        
        endpoint_result = await self.session.execute(endpoint_statement)
        top_endpoints = [
            {"path": row[0], "count": row[1]}
            for row in endpoint_result.all()
        ]
        
        # Status code distribution
        status_statement = select(
            RequestLog.status_code,
            func.count(RequestLog.id).label("count")
        ).where(
            RequestLog.timestamp >= cutoff
        ).group_by(RequestLog.status_code)
        
        status_result = await self.session.execute(status_statement)
        status_distribution = {
            row[0]: row[1]
            for row in status_result.all()
        }
        
        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "average_response_time_ms": round(avg_response_time, 2) if avg_response_time else 0,
            "requests_by_partner": requests_by_partner,
            "top_endpoints": top_endpoints,
            "status_distribution": status_distribution
        }
