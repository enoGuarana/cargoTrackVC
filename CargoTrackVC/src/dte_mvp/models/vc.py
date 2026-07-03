"""Verifiable Credential data models for cargo tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dte_mvp.core.constants import StatusOperacao, TipoVC


class VCProof(BaseModel):
    """Data Integrity proof block for a Verifiable Credential."""

    model_config = ConfigDict(frozen=True)

    type: str = Field(default="DataIntegrityProof")
    cryptosuite: str = Field(default="ecdsa-rdfc-2019")
    created: datetime
    verificationMethod: str
    proofPurpose: str = Field(default="assertionMethod")
    proofValue: str


class VCBase(BaseModel):
    """Base model for all Verifiable Credentials."""

    model_config = ConfigDict(frozen=True)

    id: str
    type: list[str]
    issuer: str
    validFrom: datetime
    validUntil: datetime | None = None
    credentialSubject: dict[str, Any]
    proof: VCProof


class VCOrdemTransporte(BaseModel):
    """Credential describing the accepted transport order."""

    model_config = ConfigDict(frozen=True)

    idOrdem: UUID
    numeroOrdem: str
    origem: str
    destino: str
    descricaoCarga: str
    quantidade: float
    unidade: str
    placa: str
    motoristaCPF: str
    embarcador: str
    transportadora: str
    recebedor: str
    status: StatusOperacao


class VCComprovanteEntrega(BaseModel):
    """Proof-of-delivery credential signed after receiver confirmation."""

    model_config = ConfigDict(frozen=True)

    idOrdem: UUID
    numeroOrdem: str
    recebedorNome: str
    documentoRecebedor: str
    entregueEm: datetime
    observacao: str | None = None


class VCEventoLogistico(BaseModel):
    """Simple logistics event credential."""

    model_config = ConfigDict(frozen=True)

    tipo: TipoVC
    evento: str
    ator: str
    dataEvento: datetime
    situacao: str


class VerifiablePresentation(BaseModel):
    """Verifiable Presentation (VP) for offline verification."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    type: list[str] = Field(default=["VerifiablePresentation"])
    holder: str
    verifiableCredential: list[VCBase]
    proof: VCProof


