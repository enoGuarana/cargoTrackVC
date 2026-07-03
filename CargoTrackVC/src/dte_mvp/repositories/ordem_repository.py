"""Repository for cargo transport orders."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from dte_mvp.core.constants import StatusOperacao
from dte_mvp.infra.database.models import OrdemORM, IdempotencyKeyORM
from dte_mvp.models.ordem import OrdemTransporte, OrdemTransporteEntrada


class OrdemRepository:
    """Repository for transport order operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, ordem_id: UUID) -> OrdemORM | None:
        """Get order by ID."""
        return self._session.get(OrdemORM, str(ordem_id))

    def get_by_chave_ordem(self, chave_ordem: str) -> OrdemORM | None:
        """Get order by idempotency key."""
        stmt = select(OrdemORM).where(OrdemORM.chave_ordem == chave_ordem)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_active_by_motorista_hash(self, cpf_hash: str) -> list[OrdemORM]:
        """Get active orders for a driver by CPF hash."""
        stmt = (
            select(OrdemORM)
            .where(
                OrdemORM.status.in_([StatusOperacao.ACEITA.value, StatusOperacao.EM_TRANSITO.value]),
                OrdemORM.participantes_minimizados["cpf_motorista_hash"].as_string() == cpf_hash,
            )
        )
        return list(self._session.execute(stmt).scalars().all())

    def get_by_idempotency_key(self, chave_ordem: str) -> str | None:
        """Check if an order was already created."""
        key = self._session.get(IdempotencyKeyORM, chave_ordem)
        return key.dte_id if key else None

    def save(self, ordem: OrdemTransporte, payload: OrdemTransporteEntrada) -> OrdemORM:
        """Save transport order to database."""
        orm = OrdemORM(
            id=str(ordem.id),
            numero_ordem=ordem.numero_ordem,
            chave_ordem=ordem.chave_ordem,
            status=ordem.status.value,
            data_criacao=ordem.data_criacao,
            data_atualizacao=ordem.data_atualizacao,
            vc_ordem_id=ordem.vc_ordem_id,
            vc_comprovante_id=ordem.vc_comprovante_id,
            vc_evento_ids=ordem.vc_evento_ids,
            hash_ordem=ordem.hash_ordem,
            participantes_minimizados=ordem.participantes_minimizados,
            ordem_payload=payload.model_dump(mode="json"),
        )
        self._session.add(orm)
        self._session.flush()
        return orm

    def save_idempotency_key(self, chave_ordem: str, ordem_id: str) -> None:
        """Save idempotency key to prevent duplicate order creation."""
        key = IdempotencyKeyORM(chave_ordem=chave_ordem, dte_id=ordem_id)
        self._session.add(key)

    def update_status(self, ordem_id: UUID, status: str) -> None:
        """Update order status."""
        orm = self.get_by_id(ordem_id)
        if orm:
            orm.status = status
            orm.data_atualizacao = datetime.utcnow()

    def update_vc_ids(
        self,
        ordem_id: UUID,
        vc_ordem_id: str | None = None,
        vc_comprovante_id: str | None = None,
        vc_evento_ids: list[str] | None = None,
    ) -> None:
        """Update VC IDs associated with an order."""
        orm = self.get_by_id(ordem_id)
        if orm:
            if vc_ordem_id:
                orm.vc_ordem_id = vc_ordem_id
            if vc_comprovante_id:
                orm.vc_comprovante_id = vc_comprovante_id
            if vc_evento_ids:
                orm.vc_evento_ids = vc_evento_ids


