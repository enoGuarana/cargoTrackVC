"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter

from dte_mvp.infra.database.session import get_engine

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Health Check")
async def health_check() -> dict:
    """Check system health."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "cargotrack-vc",
    }


@router.get("/ready", summary="Readiness Probe")
async def readiness_check() -> dict:
    """Check if service is ready to accept traffic."""
    try:
        # Try to connect to database
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/live", summary="Liveness Probe")
async def liveness_check() -> dict:
    """Check if service is alive."""
    return {"status": "alive"}



