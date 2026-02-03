
import asyncio
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/api/src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from veriqo.config import get_settings
from veriqo.parts.models import Part

settings = get_settings()
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_parts():
    async with AsyncSessionLocal() as db:
        parts_data = [
            {"sku": "SCR-IP13-OEM", "name": "iPhone 13 Screen (OEM)", "quantity_on_hand": 50},
            {"sku": "BAT-IP13-HC", "name": "iPhone 13 Battery (High Cap)", "quantity_on_hand": 30},
            {"sku": "CAM-S21-REAR", "name": "Samsung S21 Rear Camera", "quantity_on_hand": 15},
            {"sku": "CHG-PORT-UNIV", "name": "Universal USB-C Port", "quantity_on_hand": 100},
            {"sku": "ADH-IP13-FRAME", "name": "iPhone 13 Frame Adhesive", "quantity_on_hand": 200},
        ]

        print("Seeding parts...")
        for p_data in parts_data:
            # Check if exists
            # We need to import select here inside the function or at top level if not circular
            from sqlalchemy import select
            result = await db.execute(select(Part).where(Part.sku == p_data["sku"]))
            existing = result.scalar_one_or_none()

            if not existing:
                part = Part(**p_data)
                db.add(part)
                print(f"Added {p_data['name']}")
            else:
                print(f"Skipping {p_data['name']} (already exists)")
        
        await db.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(seed_parts())
