"""SQLAlchemy ORM models for the cargo tracking MVP."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dte_mvp.core.constants import StatusOperacao


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class OrdemORM(Base):
    """Cargo transport order persistence model."""

    __tablename__ = "transport_orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    numero_ordem: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    chave_ordem: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=StatusOperacao.CRIADA.value
    )
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    data_atualizacao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    vc_ordem_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vc_comprovante_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vc_evento_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    hash_ordem: Mapped[str] = mapped_column(String(64), nullable=False)
    participantes_minimizados: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ordem_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def __repr__(self) -> str:
        return f"<TransportOrderORM(id={self.id}, ordem={self.numero_ordem}, status={self.status})>"


class VCRegistryORM(Base):
    """Registry of emitted Verifiable Credentials."""

    __tablename__ = "vc_registry"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dte_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    hash_vc: Mapped[str] = mapped_column(String(64), nullable=False)
    data_emissao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    validade: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    vc_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def __repr__(self) -> str:
        return f"<VCRegistryORM(id={self.id}, tipo={self.tipo})>"


class AuditLogORM(Base):
    """Immutable audit log."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    evento: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dte_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    vc_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    detalhes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    hash_previo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash_atual: Mapped[str] = mapped_column(String(64), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLogORM(evento={self.evento}, ordem_id={self.dte_id})>"


class NotificationLogORM(Base):
    """Delivery notification log."""

    __tablename__ = "notification_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dte_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    tentativas: Mapped[int] = mapped_column(default=0)
    max_tentativas: Mapped[int] = mapped_column(default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class IdempotencyKeyORM(Base):
    """Idempotency key tracking for order creation."""

    __tablename__ = "idempotency_keys"

    chave_ordem: Mapped[str] = mapped_column(String(64), primary_key=True)
    dte_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


