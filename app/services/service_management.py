"""
Service Management - Business logic for backend services
"""
from typing import Optional, List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.service import Service, ServiceCreate


class ServiceManagementService:
    """Service for managing backend services"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_service(self, service_data: ServiceCreate) -> Service:
        """Create a new service"""
        service = Service(**service_data.model_dump())
        self.session.add(service)
        await self.session.commit()
        await self.session.refresh(service)
        return service
    
    async def get_service_by_id(self, service_id: int) -> Optional[Service]:
        """Get a service by ID"""
        return await self.session.get(Service, service_id)
    
    async def get_service_by_name(self, name: str) -> Optional[Service]:
        """Get a service by name"""
        statement = select(Service).where(Service.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_all_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services with pagination"""
        statement = select(Service).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
