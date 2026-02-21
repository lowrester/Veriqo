import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from veriqko.auth.password import hash_password
from veriqko.db.base import async_session_factory
from veriqko.devices.models import Brand, Device, GadgetType
from veriqko.jobs.models import JobStatus
from veriqko.stations.models import Station
from veriqko.users.models import User, UserRole


async def seed_data():
    print("Seeding development data...")
    async with async_session_factory() as session:
        # 1. Create Admin User
        admin_email = "admin@veriqko.com"
        admin_pass = "admin123!"

        # Check if exists
        from sqlalchemy import select
        stmt = select(User).where(User.email == admin_email)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            admin = User(
                id=str(uuid4()),
                email=admin_email,
                hashed_password=hash_password(admin_pass),
                full_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin)
            print(f"Created admin: {admin_email} / {admin_pass}")

        # 2. Create Brands
        brands = ["Apple", "Samsung", "Sony", "Google"]
        for b_name in brands:
            stmt = select(Brand).where(Brand.name == b_name)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(Brand(id=str(uuid4()), name=b_name))

        # 3. Create Gadget Types
        types = ["Mobile", "Tablet", "Console", "Laptop"]
        for t_name in types:
            stmt = select(GadgetType).where(GadgetType.name == t_name)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(GadgetType(id=str(uuid4()), name=t_name))

        # 4. Create Stations
        stations = [
            ("Intake S1", JobStatus.INTAKE),
            ("Reset S2", JobStatus.RESET),
            ("Functional S3", JobStatus.FUNCTIONAL),
            ("QC S4", JobStatus.QC)
        ]
        for name, job_status in stations:
            stmt = select(Station).where(Station.name == name)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(Station(
                    id=str(uuid4()),
                    name=name,
                    station_type=job_status,
                    is_active=True,
                    capabilities=[]
                ))

        # 5. Create a specific Device for testing
        apple_stmt = select(Brand).where(Brand.name == "Apple")
        mobile_stmt = select(GadgetType).where(GadgetType.name == "Mobile")
        apple = (await session.execute(apple_stmt)).scalar_one()
        mobile = (await session.execute(mobile_stmt)).scalar_one()

        stmt = select(Device).where(Device.model == "iPhone 15")
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(Device(
                id=str(uuid4()),
                brand_id=apple.id,
                type_id=mobile.id,
                model="iPhone 15"
            ))

        await session.commit()
    print("Data seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
