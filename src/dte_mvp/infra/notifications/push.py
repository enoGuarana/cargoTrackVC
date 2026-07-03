"""Push notification service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

from dte_mvp.core.exceptions import NotificationError
from dte_mvp.infra.config import get_settings

logger = structlog.get_logger()


class PushNotificationService(ABC):
    """Abstract push notification service."""

    @abstractmethod
    async def send(
        self,
        ordem_id: str,
        recipient_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Send push notification.

        Args:
            ordem_id: Transport order identifier.
            recipient_id: Driver/recipient identifier.
            payload: Notification payload.

        Raises:
            NotificationError: If sending fails.
        """
        ...


class FirebasePushService(PushNotificationService):
    """Firebase Cloud Messaging push notification service."""

    def __init__(self) -> None:
        self._initialized = False
        self._credentials_path = get_settings().notifications.firebase_credentials

    async def send(
        self,
        ordem_id: str,
        recipient_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Send via Firebase Cloud Messaging."""
        try:
            # In production: initialize firebase_admin and send message
            # For MVP: simulate success
            logger.info(
                "notification.sent",
                provider="firebase",
                ordem_id=ordem_id,
                recipient=recipient_id,
            )
        except Exception as e:
            raise NotificationError(
                message=f"Failed to send push notification: {e}",
                recipient=recipient_id,
            ) from e


class MockPushService(PushNotificationService):
    """Mock push notification service for testing."""

    def __init__(self) -> None:
        self.sent_notifications: list[dict[str, Any]] = []

    async def send(
        self,
        ordem_id: str,
        recipient_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Record notification for testing."""
        self.sent_notifications.append({
            "ordem_id": ordem_id,
            "recipient_id": recipient_id,
            "payload": payload,
        })
        logger.info(
            "notification.mock_sent",
            ordem_id=ordem_id,
            recipient=recipient_id,
        )


# Singleton
_notification_service: PushNotificationService | None = None


def get_notification_service() -> PushNotificationService:
    """Get the configured notification service."""
    global _notification_service
    if _notification_service is None:
        settings = get_settings()
        if settings.notifications.push_provider == "firebase":
            _notification_service = FirebasePushService()
        else:
            _notification_service = MockPushService()
    return _notification_service


def reset_notification_service() -> None:
    """Reset notification service (for testing)."""
    global _notification_service
    _notification_service = None


