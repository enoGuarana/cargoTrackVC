"""Cargo tracking API routes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from dte_mvp.core.exceptions import NotFoundError, ValidationError
from dte_mvp.models.ordem import AssinaturaEntregaEntrada, OrdemTransporteEntrada
from dte_mvp.services.ordem_service import OrdemService

router = APIRouter(prefix="/ordens", tags=["Ordens de Transporte"])


class OrdemCreateResponse(BaseModel):
    """Response for order creation."""

    ordem_id: str
    status: str
    message: str


class OrdemAceiteResponse(BaseModel):
    """Response for carrier acceptance."""

    ordem_id: str
    status: str
    vc_ordem_id: str


class DocumentoMotoristaResponse(BaseModel):
    """Credentials returned to the driver's wallet."""

    ordem_id: str
    vc_ordem_id: str | None
    vc_comprovante_id: str | None
    vc_evento_ids: list[str]
    download_url: str
    verifiableCredential: list[dict[str, Any]] = Field(default_factory=list)


class OrdemSummaryResponse(BaseModel):
    """Summary of active cargo orders for the driver."""

    ordem_id: str
    status: str
    numero_ordem: str
    origem: str | None
    destino: str | None
    descricao_carga: str | None
    vc_ordem_id: str | None
    vc_comprovante_id: str | None
    vc_evento_ids: list[str]
    download_url: str
    data_criacao: str | None


class EntregaResponse(BaseModel):
    """Response after receiver signs delivery."""

    ordem_id: str
    status: str
    vc_comprovante_id: str
    verifiableCredential: list[dict[str, Any]]


@router.post(
    "",
    response_model=OrdemCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar ordem de transporte",
    description="Endpoint usado pelo embarcador para registrar uma ordem de transporte.",
)
async def criar_ordem(payload: OrdemTransporteEntrada) -> OrdemCreateResponse:
    """Create the cargo transport order."""
    service = OrdemService()
    result = await service.criar_ordem(payload)

    if result.is_failure:
        error = result.error
        if isinstance(error, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": error.code, "message": error.message},
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": str(error)},
        )

    ordem = result.value
    return OrdemCreateResponse(
        ordem_id=str(ordem.id),
        status=ordem.status.value,
        message="Ordem de transporte criada pelo embarcador.",
    )


@router.post(
    "/{ordem_id}/aceite",
    response_model=OrdemAceiteResponse,
    summary="Aceitar ordem pela transportadora",
    description="A transportadora aceita a carga e o sistema emite o documento digital do motorista.",
)
async def aceitar_ordem(ordem_id: UUID) -> OrdemAceiteResponse:
    """Accept the transport order and emit the driver's credential."""
    service = OrdemService()
    result = await service.aceitar_ordem(ordem_id)
    if result.is_failure:
        error = result.error
        status_code = status.HTTP_404_NOT_FOUND if isinstance(error, NotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=status_code, detail={"message": str(error)})
    return OrdemAceiteResponse(**result.value)


@router.get(
    "",
    response_model=list[OrdemSummaryResponse],
    summary="Listar ordens ativas do motorista",
    description="Retorna ordens aceitas ou em transito vinculadas ao CPF do motorista.",
)
async def listar_ordens(cpf: str = Query(..., min_length=11, max_length=11)) -> list[OrdemSummaryResponse]:
    """List active cargo orders for a driver using CPF."""
    service = OrdemService()
    return [OrdemSummaryResponse(**item) for item in await service.listar_ordens_motorista(cpf)]


@router.get(
    "/{ordem_id}/documento",
    response_model=DocumentoMotoristaResponse,
    summary="Baixar documento digital do motorista",
    description="Endpoint autenticado para a wallet do motorista baixar VCs da ordem.",
)
async def baixar_documento(ordem_id: UUID, cpf: str) -> DocumentoMotoristaResponse:
    """Download VCs for the driver's wallet."""
    service = OrdemService()
    result = await service.entregar_documento_motorista(ordem_id, cpf)
    if result.is_failure:
        error = result.error
        status_code = status.HTTP_404_NOT_FOUND if isinstance(error, NotFoundError) else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail={"message": str(error)})
    return DocumentoMotoristaResponse(**result.value)


@router.post(
    "/{ordem_id}/entrega",
    response_model=EntregaResponse,
    summary="Assinar entrega pelo recebedor",
    description="Registra a assinatura do recebedor e emite o comprovante verificavel final.",
)
async def assinar_entrega(ordem_id: UUID, payload: AssinaturaEntregaEntrada) -> EntregaResponse:
    """Register receiver signature and issue proof of delivery."""
    service = OrdemService()
    result = await service.assinar_entrega(ordem_id, payload)
    if result.is_failure:
        error = result.error
        status_code = status.HTTP_404_NOT_FOUND if isinstance(error, NotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=status_code, detail={"message": str(error)})
    return EntregaResponse(**result.value)


@router.get(
    "/{ordem_id}/status",
    summary="Consultar status da ordem",
    description="Consulta o status atual da operacao de transporte.",
)
async def consultar_status(ordem_id: UUID) -> dict:
    """Check order status."""
    from dte_mvp.infra.database.session import db_session
    from dte_mvp.repositories.ordem_repository import OrdemRepository

    with db_session() as session:
        repo = OrdemRepository(session)
        orm = repo.get_by_id(ordem_id)
        if not orm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": f"Ordem nao encontrada: {ordem_id}"},
            )
        return {
            "ordem_id": str(ordem_id),
            "status": orm.status,
            "numero_ordem": orm.numero_ordem,
            "origem": orm.ordem_payload.get("origem"),
            "destino": orm.ordem_payload.get("destino"),
            "data_criacao": orm.data_criacao.isoformat() if orm.data_criacao else None,
            "data_atualizacao": orm.data_atualizacao.isoformat() if orm.data_atualizacao else None,
        }


