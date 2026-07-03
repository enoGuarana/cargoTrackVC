"""Celery tasks for asynchronous cargo tracking processing."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from dte_mvp.core.exceptions import NotificationError
from dte_mvp.infra.notifications.push import get_notification_service
from dte_mvp.infra.queue.celery_app import get_celery_app
from dte_mvp.models.ordem import OrdemTransporteEntrada
from dte_mvp.services.ordem_service import OrdemService

logger = structlog.get_logger()
celery = get_celery_app()


@celery.task(bind=True, max_retries=3)
def process_order_async(self, ordem_data: dict[str, Any]) -> dict[str, Any]:
    """Create a transport order asynchronously."""
    try:
        ordem = OrdemTransporteEntrada(**ordem_data)
        result = asyncio.run(_process_order(ordem))
        return result
    except Exception as exc:
        logger.error("task.process_order.failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


async def _process_order(ordem: OrdemTransporteEntrada) -> dict[str, Any]:
    """Internal async processing of an order."""
    service = OrdemService()
    result = await service.criar_ordem(ordem)

    if result.is_failure:
        error = result.error
        return {"status": "error", "message": str(error), "code": getattr(error, "code", "ERROR")}

    created = result.value
    return {"status": "success", "ordem_id": str(created.id)}


@celery.task(bind=True, max_retries=3)
def send_push_notification(self, ordem_id: str, recipient_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Send notification to the driver wallet."""
    try:
        notif_service = get_notification_service()
        asyncio.run(notif_service.send(ordem_id, recipient_id, payload))
        return {"status": "sent", "ordem_id": ordem_id}
    except NotificationError as exc:
        logger.error("task.notification.failed", ordem_id=ordem_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)
    except Exception as exc:
        logger.error("task.notification.unexpected_error", ordem_id=ordem_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery.task
def register_logistics_event_task(ordem_id: str, evento: str, actor: str) -> dict[str, Any]:
    """Small example task for async logistics event registration."""
    return {
        "status": "registered",
        "ordem_id": ordem_id,
        "evento": evento,
        "actor": actor,
    }


