"""CargoTrack VC FastAPI application entry point."""

from __future__ import annotations

import structlog
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from dte_mvp.api.middleware import setup_middleware
from dte_mvp.api.routes.ordens import router as ordem_router
from dte_mvp.api.routes.health import router as health_router
from dte_mvp.api.routes.public_keys import router as public_keys_router
from dte_mvp.infra.config import get_settings
from dte_mvp.infra.database.session import init_db

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CargoTrack VC API",
        description="Sistema didatico para rastreamento de carga e comprovante verificavel",
        version=settings.app.version,
        docs_url=settings.api.docs_url,
        redoc_url=settings.api.redoc_url,
        openapi_url=settings.api.openapi_url,
    )

    # Setup middleware
    setup_middleware(app)

    # Include routers
    app.include_router(health_router, prefix=settings.api.prefix)
    app.include_router(ordem_router, prefix=settings.api.prefix)
    app.include_router(public_keys_router, prefix=settings.api.prefix)

    # Mount prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    @app.on_event("startup")
    async def startup() -> None:
        """Initialize application on startup."""
        logger.info("app.startup", version=settings.app.version, env=settings.app.env)
        init_db()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        """Cleanup on shutdown."""
        logger.info("app.shutdown")

    return app


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    app = create_app()

    uvicorn.run(
        "dte_mvp.main:create_app",
        host=settings.server.host,
        port=settings.server.port,
        workers=settings.server.workers if not settings.app.debug else 1,
        reload=settings.server.reload,
        factory=True,
    )


if __name__ == "__main__":
    main()



