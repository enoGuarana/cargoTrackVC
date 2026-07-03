"""Celery application configuration."""

from __future__ import annotations

from celery import Celery

from dte_mvp.infra.config import get_settings

celery_app: Celery | None = None


def get_celery_app() -> Celery:
    """Get or create the Celery application instance."""
    global celery_app
    if celery_app is None:
        settings = get_settings()
        cfg = settings.queue

        celery_app = Celery("cargotrack_vc")
        celery_app.conf.update(
            broker_url=cfg.broker_url,
            result_backend=cfg.result_backend,
            task_serializer=cfg.task_serializer,
            accept_content=cfg.accept_content,
            result_serializer=cfg.result_serializer,
            timezone=cfg.timezone,
            enable_utc=cfg.enable_utc,
            task_track_started=cfg.task_track_started,
            task_time_limit=cfg.task_time_limit,
            worker_prefetch_multiplier=cfg.worker_prefetch_multiplier,
            task_always_eager=cfg.task_always_eager,
            task_store_eager_result=cfg.task_store_eager_result,
        )

        # Auto-discover tasks
        celery_app.autodiscover_tasks(["dte_mvp.infra.queue.tasks"])

    return celery_app

# Celery app exposed for the worker CLI.
celery = get_celery_app()


