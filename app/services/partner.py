"""
Partner Service - Business logic for partner management
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.partner import Partner, PartnerCreate, PartnerUpdate
from app.models.permission import PartnerServicePermission


class PartnerService:
    """Service for managing partners"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_partner(self, partner_data: PartnerCreate) -> tuple[Partner, str]:
        """
        Create a new partner with API key and service permissions
        Returns: (partner, api_key) - API key is only returned once
        """
        api_key = Partner.generate_api_key()
        api_key_hash = Partner.hash_api_key(api_key)
        
        partner = Partner(
            name=partner_data.name,
            rate_limit=partner_data.rate_limit,
            api_key_hash=api_key_hash
        )
        
        self.session.add(partner)
        await self.session.commit()
        await self.session.refresh(partner)
        
        # Grant service permissions
        for service_id in partner_data.service_ids:
            permission = PartnerServicePermission(
                partner_id=partner.id,
                service_id=service_id
            )
            self.session.add(permission)
        
        await self.session.commit()
        
        return partner, api_key
    
    async def create_partner_with_key(self, partner_data: PartnerCreate, api_key: str) -> Partner:
        """Create a partner with a specific API key (for seeding)"""
        api_key_hash = Partner.hash_api_key(api_key)
        
        partner = Partner(
            name=partner_data.name,
            rate_limit=partner_data.rate_limit,
            api_key_hash=api_key_hash
        )
        
        self.session.add(partner)
        await self.session.commit()
        await self.session.refresh(partner)
        
        # Grant service permissions
        for service_id in partner_data.service_ids:
            permission = PartnerServicePermission(
                partner_id=partner.id,
                service_id=service_id
            )
            self.session.add(permission)
        
        await self.session.commit()
        
        return partner
    
    async def get_partner_by_id(self, partner_id: int) -> Optional[Partner]:
        """Get a partner by ID"""
        return await self.session.get(Partner, partner_id)
    
    async def get_partner_by_api_key(self, api_key: str) -> Optional[Partner]:
        """Get a partner by API key"""
        api_key_hash = Partner.hash_api_key(api_key)
        statement = select(Partner).where(Partner.api_key_hash == api_key_hash)
        result = await self.session.execute(statement)
        partner = result.scalar_one_or_none()
        
        if partner:
            # Populate allowed services
            partner.allowed_services = await self.get_partner_services(partner.id)
        
        return partner
    
    async def get_all_partners(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all partners with their allowed services"""
        statement = select(Partner).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        partners = list(result.scalars().all())
        
        # Populate allowed services for each partner
        partners_with_services = []
        for partner in partners:
            services = await self.get_partner_services(partner.id)
            partners_with_services.append({
                "id": partner.id,
                "name": partner.name,
                "rate_limit": partner.rate_limit,
                "is_active": partner.is_active,
                "allowed_services": services,
                "created_at": partner.created_at,
                "updated_at": partner.updated_at,
                "api_key_hash": partner.api_key_hash
            })
        
        return partners_with_services
    
    async def get_active_partners(self) -> List[Partner]:
        """Get all active partners"""
        statement = select(Partner).where(Partner.is_active == True)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
    
    async def update_partner(self, partner_id: int, partner_data: PartnerUpdate) -> Optional[Partner]:
        """Update a partner"""
        partner = await self.session.get(Partner, partner_id)
        if not partner:
            return None
        
        update_data = partner_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(partner, key, value)
        
        from datetime import datetime
        partner.updated_at = datetime.utcnow()
        
        self.session.add(partner)
        await self.session.commit()
        await self.session.refresh(partner)
        
        return partner
    
    async def deactivate_partner(self, partner_id: int) -> bool:
        """Deactivate a partner"""
        partner = await self.session.get(Partner, partner_id)
        if not partner:
            return False
        
        partner.is_active = False
        self.session.add(partner)
        await self.session.commit()
        
        return True
    
    async def regenerate_api_key(self, partner_id: int) -> Optional[str]:
        """Regenerate API key for a partner"""
        partner = await self.session.get(Partner, partner_id)
        if not partner:
            return None
        
        new_api_key = Partner.generate_api_key()
        partner.api_key_hash = Partner.hash_api_key(new_api_key)
        
        from datetime import datetime
        partner.updated_at = datetime.utcnow()
        
        self.session.add(partner)
        await self.session.commit()
        
        return new_api_key
    
    async def get_partner_services(self, partner_id: int) -> List[str]:
        """Get list of service names a partner can access"""
        from app.models.service import Service
        
        statement = select(Service.name).join(
            PartnerServicePermission,
            Service.id == PartnerServicePermission.service_id
        ).where(
            PartnerServicePermission.partner_id == partner_id
        )
        
        result = await self.session.execute(statement)
        return list(result.scalars().all())
    
    async def can_access_service(self, partner_id: int, service_name: str) -> bool:
        """Check if partner has permission to access a service"""
        from app.models.service import Service
        
        statement = select(PartnerServicePermission).join(
            Service,
            Service.id == PartnerServicePermission.service_id
        ).where(
            PartnerServicePermission.partner_id == partner_id,
            Service.name == service_name,
            Service.is_active == True
        )
        
        result = await self.session.execute(statement)
        permission = result.scalar_one_or_none()
        
        return permission is not None
    
    async def grant_service_access(self, partner_id: int, service_id: int) -> bool:
        """Grant partner access to a service"""
        # Check if permission already exists
        statement = select(PartnerServicePermission).where(
            PartnerServicePermission.partner_id == partner_id,
            PartnerServicePermission.service_id == service_id
        )
        result = await self.session.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            return False
        
        permission = PartnerServicePermission(
            partner_id=partner_id,
            service_id=service_id
        )
        self.session.add(permission)
        await self.session.commit()
        
        return True
    
    async def revoke_service_access(self, partner_id: int, service_id: int) -> bool:
        """Revoke partner access to a service"""
        statement = select(PartnerServicePermission).where(
            PartnerServicePermission.partner_id == partner_id,
            PartnerServicePermission.service_id == service_id
        )
        result = await self.session.execute(statement)
        permission = result.scalar_one_or_none()
        
        if not permission:
            return False
        
        await self.session.delete(permission)
        await self.session.commit()
        
        return True
