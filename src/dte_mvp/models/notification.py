"""Notification models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationStatus(str, Enum):
    """Status of a push notification."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class PushNotification(BaseModel):
    """Push notification to be sent to the driver app."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=lambda: __import__("uuid").uuid4())
    dte_id: UUID
    recipient_id: str
    payload: dict
    status: NotificationStatus = NotificationStatus.PENDING
    tentativas: int = 0
    max_tentativas: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: datetime | None = None
    error_message: str | None = None


