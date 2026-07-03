"""Cargo tracking domain models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from dte_mvp.core.constants import StatusOperacao


class OrdemTransporteEntrada(BaseModel):
    """Order created by the shipper before the carrier accepts the load."""

    model_config = ConfigDict(frozen=True)

    numero_ordem: str = Field(..., min_length=3, max_length=40)
    chave_ordem: str = Field(..., min_length=8, max_length=64)
    embarcador: str
    cnpj_embarcador: str = Field(..., pattern=r"^\d{14}$")
    transportadora: str
    cnpj_transportadora: str = Field(..., pattern=r"^\d{14}$")
    motorista_nome: str
    cpf_motorista: str = Field(..., pattern=r"^\d{11}$")
    placa: str = Field(..., pattern=r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")
    recebedor: str
    cnpj_recebedor: str = Field(..., pattern=r"^\d{14}$")
    origem: str
    destino: str
    descricao_carga: str
    quantidade: float = Field(..., gt=0)
    unidade: str
    valor_frete: float = Field(..., ge=0)
    data_coleta_prevista: datetime


class AssinaturaEntregaEntrada(BaseModel):
    """Delivery confirmation signed by the receiver."""

    recebedor_nome: str
    documento_recebedor: str = Field(..., min_length=5, max_length=20)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    observacao: str | None = Field(default=None, max_length=500)


class OrdemTransporte(BaseModel):
    """Aggregate root for a cargo transport order."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    numero_ordem: str
    chave_ordem: str
    status: StatusOperacao = StatusOperacao.CRIADA
    data_criacao: datetime = Field(default_factory=datetime.utcnow)
    data_atualizacao: datetime | None = None
    vc_ordem_id: str | None = None
    vc_comprovante_id: str | None = None
    vc_evento_ids: list[str] = Field(default_factory=list)
    hash_ordem: str
    participantes_minimizados: dict = Field(default_factory=dict)


class OrdemCreateRequest(BaseModel):
    """Request to create a new transport order."""

    model_config = ConfigDict(frozen=True)

    ordem: OrdemTransporteEntrada



