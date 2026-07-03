"""Cargo tracking core business service."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

import structlog

from dte_mvp.core.constants import EventoAuditoria, StatusOperacao
from dte_mvp.core.exceptions import NotFoundError, ValidationError
from dte_mvp.core.result import Result
from dte_mvp.infra.database.session import db_session
from dte_mvp.models.ordem import AssinaturaEntregaEntrada, OrdemTransporte, OrdemTransporteEntrada
from dte_mvp.repositories.ordem_repository import OrdemRepository
from dte_mvp.repositories.vc_repository import VCRepository
from dte_mvp.services.audit_service import AuditService
from dte_mvp.services.vc_service import VCService

logger = structlog.get_logger()


class OrdemService:
    """Service for the cargo transport order lifecycle."""

    def __init__(self) -> None:
        self._vc_service = VCService()
        self._audit = AuditService()

    async def criar_ordem(self, entrada: OrdemTransporteEntrada) -> Result[OrdemTransporte, Exception]:
        """Create a transport order from the shipper request."""
        try:
            with db_session() as session:
                repo = OrdemRepository(session)
                existing_id = repo.get_by_idempotency_key(entrada.chave_ordem)
                if existing_id:
                    existing = repo.get_by_id(UUID(existing_id))
                    if existing:
                        logger.info("ordem.idempotency_hit", chave=entrada.chave_ordem)
                        return Result.success(self._to_domain(existing))

            ordem_hash = hashlib.sha256(
                json.dumps(entrada.model_dump(mode="json"), sort_keys=True).encode()
            ).hexdigest()
            ordem = OrdemTransporte(
                numero_ordem=entrada.numero_ordem,
                chave_ordem=entrada.chave_ordem,
                hash_ordem=ordem_hash,
                participantes_minimizados={
                    "cpf_motorista_hash": hashlib.sha256(entrada.cpf_motorista.encode()).hexdigest()[:16],
                    "cnpj_embarcador_hash": hashlib.sha256(entrada.cnpj_embarcador.encode()).hexdigest()[:16],
                    "cnpj_transportadora_hash": hashlib.sha256(entrada.cnpj_transportadora.encode()).hexdigest()[:16],
                },
            )

            with db_session() as session:
                repo = OrdemRepository(session)
                repo.save(ordem, entrada)
                repo.save_idempotency_key(entrada.chave_ordem, str(ordem.id))

            self._audit.log_event(
                EventoAuditoria.ORDEM_CRIADA,
                dte_id=ordem.id,
                actor="embarcador",
                detalhes={"numero_ordem": entrada.numero_ordem, "origem": entrada.origem, "destino": entrada.destino},
            )
            return Result.success(ordem)

        except Exception as exc:
            logger.error("ordem.creation_failed", error=str(exc))
            return Result.failure(exc)

    async def aceitar_ordem(self, ordem_id: UUID) -> Result[dict[str, Any], Exception]:
        """Accept an order and issue the driver's digital transport document."""
        try:
            with db_session() as session:
                repo = OrdemRepository(session)
                orm = repo.get_by_id(ordem_id)
                if not orm:
                    return Result.failure(NotFoundError(f"Ordem nao encontrada: {ordem_id}"))
                if orm.status not in {StatusOperacao.CRIADA.value, StatusOperacao.ACEITA.value}:
                    return Result.failure(ValidationError("Apenas ordens criadas podem ser aceitas"))

                entrada = OrdemTransporteEntrada(**orm.ordem_payload)
                vc_ordem = self._vc_service.gerar_vc_ordem_transporte(entrada, ordem_id)
                vc_evento = self._vc_service.gerar_vc_evento_logistico(
                    ordem_id, "ordem_aceita", entrada.transportadora, "ACEITA"
                )

                vc_repo = VCRepository(session)
                vc_repo.save(
                    vc_ordem["id"],
                    "VC-OrdemTransporte",
                    str(ordem_id),
                    self._vc_service.calcular_hash(vc_ordem),
                    vc_metadata={"document": vc_ordem},
                )
                vc_repo.save(
                    vc_evento["id"],
                    "VC-EventoLogistico",
                    str(ordem_id),
                    self._vc_service.calcular_hash(vc_evento),
                    vc_metadata={"document": vc_evento},
                )
                repo.update_status(ordem_id, StatusOperacao.ACEITA.value)
                repo.update_vc_ids(ordem_id, vc_ordem_id=vc_ordem["id"], vc_evento_ids=[vc_evento["id"]])

            self._audit.log_event(
                EventoAuditoria.ORDEM_ACEITA,
                dte_id=ordem_id,
                vc_id=vc_ordem["id"],
                actor="transportadora",
            )
            return Result.success({"ordem_id": str(ordem_id), "status": "aceita", "vc_ordem_id": vc_ordem["id"]})
        except Exception as exc:
            logger.error("ordem.accept_failed", error=str(exc), ordem_id=str(ordem_id))
            return Result.failure(exc)

    async def entregar_documento_motorista(self, ordem_id: UUID, cpf: str) -> Result[dict[str, Any], Exception]:
        """Return the accepted order credentials to the driver's wallet."""
        cpf_hash = hashlib.sha256(cpf.encode()).hexdigest()[:16]

        with db_session() as session:
            repo = OrdemRepository(session)
            orm = repo.get_by_id(ordem_id)
            if not orm:
                return Result.failure(NotFoundError(f"Ordem nao encontrada: {ordem_id}"))
            if orm.participantes_minimizados.get("cpf_motorista_hash") != cpf_hash:
                return Result.failure(NotFoundError("Ordem nao encontrada para este motorista"))

            vc_repo = VCRepository(session)
            vcs = vc_repo.get_by_dte(ordem_id)
            documents = [vc.vc_metadata.get("document") for vc in vcs if vc.vc_metadata.get("document")]

        self._audit.log_event(EventoAuditoria.DOCUMENTO_BAIXADO, dte_id=ordem_id, actor="motorista")
        return Result.success({
            "ordem_id": str(ordem_id),
            "vc_ordem_id": orm.vc_ordem_id,
            "vc_comprovante_id": orm.vc_comprovante_id,
            "vc_evento_ids": orm.vc_evento_ids,
            "download_url": f"/api/v1/ordens/{ordem_id}/documento",
            "verifiableCredential": documents,
        })

    async def assinar_entrega(
        self,
        ordem_id: UUID,
        assinatura: AssinaturaEntregaEntrada,
    ) -> Result[dict[str, Any], Exception]:
        """Register receiver signature and issue final proof of delivery."""
        try:
            with db_session() as session:
                repo = OrdemRepository(session)
                orm = repo.get_by_id(ordem_id)
                if not orm:
                    return Result.failure(NotFoundError(f"Ordem nao encontrada: {ordem_id}"))
                if orm.status not in {StatusOperacao.ACEITA.value, StatusOperacao.EM_TRANSITO.value}:
                    return Result.failure(ValidationError("Entrega so pode ser assinada em ordem aceita ou em transito"))

                entrada = OrdemTransporteEntrada(**orm.ordem_payload)
                vc_entrega = self._vc_service.gerar_vc_comprovante_entrega(entrada, ordem_id, assinatura)
                vc_evento = self._vc_service.gerar_vc_evento_logistico(
                    ordem_id, "entrega_assinada", assinatura.recebedor_nome, "ENTREGUE"
                )

                vc_repo = VCRepository(session)
                vc_repo.save(
                    vc_entrega["id"],
                    "VC-ComprovanteEntrega",
                    str(ordem_id),
                    self._vc_service.calcular_hash(vc_entrega),
                    vc_metadata={"document": vc_entrega},
                )
                vc_repo.save(
                    vc_evento["id"],
                    "VC-EventoLogistico",
                    str(ordem_id),
                    self._vc_service.calcular_hash(vc_evento),
                    vc_metadata={"document": vc_evento},
                )
                evento_ids = list(orm.vc_evento_ids or []) + [vc_evento["id"]]
                repo.update_status(ordem_id, StatusOperacao.ENTREGUE.value)
                repo.update_vc_ids(
                    ordem_id,
                    vc_comprovante_id=vc_entrega["id"],
                    vc_evento_ids=evento_ids,
                )

            self._audit.log_event(
                EventoAuditoria.ENTREGA_ASSINADA,
                dte_id=ordem_id,
                vc_id=vc_entrega["id"],
                actor="recebedor",
            )
            return Result.success({
                "ordem_id": str(ordem_id),
                "status": "entregue",
                "vc_comprovante_id": vc_entrega["id"],
                "verifiableCredential": [vc_entrega],
            })
        except Exception as exc:
            logger.error("ordem.delivery_failed", error=str(exc), ordem_id=str(ordem_id))
            return Result.failure(exc)

    async def listar_ordens_motorista(self, cpf: str) -> list[dict[str, Any]]:
        """List active orders assigned to the driver."""
        cpf_hash = hashlib.sha256(cpf.encode()).hexdigest()[:16]
        with db_session() as session:
            repo = OrdemRepository(session)
            ordens = repo.get_active_by_motorista_hash(cpf_hash)
            return [
                {
                    "ordem_id": orm.id,
                    "status": orm.status,
                    "numero_ordem": orm.numero_ordem,
                    "origem": orm.ordem_payload.get("origem"),
                    "destino": orm.ordem_payload.get("destino"),
                    "descricao_carga": orm.ordem_payload.get("descricao_carga"),
                    "vc_ordem_id": orm.vc_ordem_id,
                    "vc_comprovante_id": orm.vc_comprovante_id,
                    "vc_evento_ids": orm.vc_evento_ids,
                    "download_url": f"/api/v1/ordens/{orm.id}/documento",
                    "data_criacao": orm.data_criacao.isoformat() if orm.data_criacao else None,
                }
                for orm in ordens
            ]

    def _to_domain(self, orm: Any) -> OrdemTransporte:
        """Convert ORM model to domain model."""
        return OrdemTransporte(
            id=UUID(orm.id),
            numero_ordem=orm.numero_ordem,
            chave_ordem=orm.chave_ordem,
            status=StatusOperacao(orm.status),
            data_criacao=orm.data_criacao,
            data_atualizacao=orm.data_atualizacao,
            vc_ordem_id=orm.vc_ordem_id,
            vc_comprovante_id=orm.vc_comprovante_id,
            vc_evento_ids=orm.vc_evento_ids,
            hash_ordem=orm.hash_ordem,
            participantes_minimizados=orm.participantes_minimizados,
        )



