"""
Seed Data - Demo partners and services for development/testing
Run with: python -m app.seed_data
"""
import asyncio
from app.database import Async_Session, create_db_and_tables
from app.models.partner import PartnerCreate
from app.models.service import ServiceCreate
from app.services.partner import PartnerService
from app.services.service_management import ServiceManagementService


async def seed_services():
    """Create backend services"""
    async with Async_Session() as session:
        service_mgmt = ServiceManagementService(session)
        
        # Check if services already exist
        existing = await service_mgmt.get_all_services()
        if existing:
            print("Services already exist, skipping service creation")
            return {s.name: s.id for s in existing}
        
        # Create services
        services = [
            ServiceCreate(name="users", display_name="Users Service", description="User management"),
            ServiceCreate(name="posts", display_name="Posts Service", description="Blog posts"),
            ServiceCreate(name="comments", display_name="Comments Service", description="Post comments"),
            ServiceCreate(name="todos", display_name="Todos Service", description="Task management"),
            ServiceCreate(name="albums", display_name="Albums Service", description="Photo albums"),
            ServiceCreate(name="photos", display_name="Photos Service", description="Photos"),
        ]
        
        service_map = {}
        for service_data in services:
            service = await service_mgmt.create_service(service_data)
            service_map[service.name] = service.id
            print(f"Created service: {service.name} (ID: {service.id})")
        
        return service_map


async def seed_demo_partners():
    """Create demo partners for testing"""
    async with Async_Session() as session:
        partner_service = PartnerService(session)
        
        # Check if partners already exist
        existing = await partner_service.get_all_partners(limit=1)
        if existing:
            print("Demo partners already exist, skipping seed")
            return
        
        # Get service IDs
        service_map = await seed_services()
        
        # Create demo partners
        demo_partners = [
            {
                "name": "Premium Partner",
                "service_names": ["users", "posts", "comments", "todos", "albums", "photos"],
                "rate_limit": 100,
                "api_key": "premium-api-key-12345"
            },
            {
                "name": "Basic Partner",
                "service_names": ["users", "posts"],
                "rate_limit": 30,
                "api_key": "basic-api-key-67890"
            },
            {
                "name": "Todo App Partner",
                "service_names": ["todos"],
                "rate_limit": 50,
                "api_key": "todo-api-key-11111"
            }
        ]
        
        for p in demo_partners:
            # Convert service names to IDs
            service_ids = [service_map[name] for name in p["service_names"] if name in service_map]
            
            # Use unified create_partner with provided demo API key
            _, created_key = await partner_service.create_partner(
                PartnerCreate(
                    name=p["name"],
                    service_ids=service_ids,
                    rate_limit=p["rate_limit"]
                ),
                api_key=p["api_key"]
            )
            print(f"Created partner: {p['name']} with key: {p['api_key']} (services: {p['service_names']})")


async def main():
    await create_db_and_tables()
    await seed_services()
    await seed_demo_partners()


if __name__ == "__main__":
    asyncio.run(main())
