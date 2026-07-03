"""Audit logging service."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog

from dte_mvp.core.constants import EventoAuditoria
from dte_mvp.infra.database.session import db_session
from dte_mvp.models.audit import AuditLogEntry
from dte_mvp.repositories.audit_repository import AuditRepository

logger = structlog.get_logger()


class AuditService:
    """Service for recording immutable audit logs."""

    def __init__(self) -> None:
        self._last_hash: str | None = None

    def log_event(
        self,
        evento: EventoAuditoria,
        dte_id: str | UUID | None = None,
        vc_id: str | None = None,
        actor: str = "system",
        detalhes: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        """Record an audit event with chain of hashes.

        Each entry includes a hash of the previous entry,
        creating an immutable chain for tamper detection.
        """
        dte_uuid = UUID(dte_id) if isinstance(dte_id, str) and dte_id else dte_id

        entry_data = {
            "evento": evento.value,
            "dte_id": str(dte_uuid) if dte_uuid else None,
            "vc_id": vc_id,
            "actor": actor,
            "detalhes": detalhes or {},
            "timestamp": datetime.now(UTC).isoformat(),
            "hash_previo": self._last_hash,
        }

        # Calculate current hash
        hash_input = json.dumps(entry_data, sort_keys=True)
        hash_atual = hashlib.sha256(hash_input.encode()).hexdigest()
        self._last_hash = hash_atual

        entry = AuditLogEntry(
            evento=evento,
            dte_id=dte_uuid,
            vc_id=vc_id,
            actor=actor,
            detalhes=detalhes or {},
            hash_previo=self._last_hash,
            hash_atual=hash_atual,
        )

        try:
            with db_session() as session:
                repo = AuditRepository(session)
                repo.save(entry)
        except Exception as e:
            # Audit logging should not fail the main operation
            logger.error("audit.log_failed", error=str(e), evento=evento.value)

        logger.info(
            "audit.event_logged",
            evento=evento.value,
            dte_id=str(dte_uuid) if dte_uuid else None,
            actor=actor,
        )
        return entry


