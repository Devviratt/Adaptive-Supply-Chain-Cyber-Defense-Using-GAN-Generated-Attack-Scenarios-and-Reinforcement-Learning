"""
ASCCD FastAPI Application.

Main entry point for the backend API server.
Provides health check, CORS, database initialization, and structured logging.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import (
    defense,
    experiments,
    health,
    project,
    scenarios,
    simulation,
)
from src.common.config import get_settings
from src.common.database import create_db_engine, init_db
from src.common.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    settings = get_settings()

    # Configure logging
    setup_logging(
        log_level=settings.log_level, log_format="console" if settings.app_debug else "json"
    )

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        debug=settings.app_debug,
    )

    # Initialize database
    engine = create_db_engine()
    init_db(engine)
    logger.info("database_initialized")

    yield

    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="ASCCD — Adaptive Supply Chain Cyber Defense",
        description=(
            "Research platform for studying GAN-generated synthetic attack scenarios "
            "and reinforcement-learning-based adaptive defense in a simulated "
            "software supply-chain environment."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("unhandled_exception", error=str(exc), path=str(request.url))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Check system logs for details."},
        )

    # Register routers
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(project.router, prefix="/api/project", tags=["Project"])
    app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])
    app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
    app.include_router(defense.router, prefix="/api/defense", tags=["Defense"])
    app.include_router(experiments.router, prefix="/api/experiments", tags=["Experiments"])

    return app


# Application instance
app = create_app()
