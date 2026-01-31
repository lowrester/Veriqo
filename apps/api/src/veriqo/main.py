"""Veriqo API - Main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from veriqo.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()

    # Ensure storage directories exist
    settings.storage_base_path.mkdir(parents=True, exist_ok=True)
    (settings.storage_base_path / "evidence").mkdir(exist_ok=True)
    (settings.storage_base_path / "reports").mkdir(exist_ok=True)

    yield

    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Veriqo API",
        description="Console Verification Platform API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from veriqo.auth.router import router as auth_router
    from veriqo.evidence.router import evidence_router, router as evidence_job_router
    from veriqo.jobs.router import router as jobs_router
    from veriqo.reports.router import public_router, router as reports_router
    from veriqo.users.router import router as users_router

    # API v1 routes
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(evidence_job_router, prefix="/api/v1")
    app.include_router(evidence_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")

    # Public routes (no /api/v1 prefix)
    app.include_router(public_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.brand_name,
            "api": f"{settings.base_url}/api/v1",
            "docs": f"{settings.base_url}/api/docs" if settings.debug else None,
        }

    return app


# Create app instance
app = create_app()
