import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from veriqko.db.base import Base, engine

# Import all models to ensure they are registered with Base.metadata


async def init_db():
    print("Initializing database...")
    async with engine.begin() as conn:
        # For SQLite, we might need to handle the UUID and JSONB types
        # SQLAlchemy usually handles them gracefully by falling back to basic types
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
