"""
Health check router.

Provides system health and readiness endpoints.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.deps import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check — confirms API is running."""
    return {
        "status": "healthy",
        "service": "ASCCD",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):  # noqa: B008
    """Readiness check — confirms API + database are operational."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "service": "ASCCD",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {
            "database": db_status,
        },
    }
