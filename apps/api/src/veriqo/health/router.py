from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from veriqo.db.base import get_db
import importlib.metadata

router = APIRouter(tags=["system"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    System health check.
    Verifies API is running and Database connection is active.
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "version": "v2.1.0"
    }
    
    try:
        # Check DB connection
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = "unreachable"
        health_status["error"] = str(e)
        
    return health_status
