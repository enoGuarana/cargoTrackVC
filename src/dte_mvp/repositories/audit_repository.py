"""Audit log repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from dte_mvp.infra.database.models import AuditLogORM
from dte_mvp.models.audit import AuditLogEntry


class AuditRepository:
    """Repository for immutable audit log entries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entry: AuditLogEntry) -> AuditLogORM:
        """Save an audit log entry.

        Audit logs are immutable - never update, only append.
        """
        orm = AuditLogORM(
            id=str(entry.id),
            timestamp=entry.timestamp,
            evento=entry.evento.value,
            dte_id=str(entry.dte_id) if entry.dte_id else None,
            vc_id=entry.vc_id,
            actor=entry.actor,
            detalhes=entry.detalhes,
            hash_previo=entry.hash_previo,
            hash_atual=entry.hash_atual,
        )
        self._session.add(orm)
        self._session.flush()
        return orm

    def get_by_dte(self, dte_id: UUID, limit: int = 100) -> list[AuditLogORM]:
        """Get audit entries for a transport order."""
        from sqlalchemy import select
        stmt = (
            select(AuditLogORM)
            .where(AuditLogORM.dte_id == str(dte_id))
            .order_by(AuditLogORM.timestamp.desc())
            .limit(limit)
        )
        return list(self._session.execute(stmt).scalars().all())


