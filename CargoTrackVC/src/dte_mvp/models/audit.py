"""Audit log models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dte_mvp.core.constants import EventoAuditoria


class AuditLogEntry(BaseModel):
    """Immutable audit log entry."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=lambda: __import__("uuid").uuid4())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evento: EventoAuditoria
    dte_id: UUID | None = None
    vc_id: str | None = None
    actor: str = "system"
    detalhes: dict[str, Any] = Field(default_factory=dict)
    hash_previo: str | None = None
    hash_atual: str


