"""System-wide constants for the cargo tracking MVP."""

from enum import Enum


class StatusOperacao(str, Enum):
    """Lifecycle status of a cargo transport order."""

    CRIADA = "criada"
    ACEITA = "aceita"
    EM_TRANSITO = "em_transito"
    ENTREGUE = "entregue"
    CANCELADA = "cancelada"


class UnidadeMedida(str, Enum):
    """Valid measurement units for cargo."""

    KG = "kg"
    TON = "ton"
    UNIDADE = "unidade"
    PALLET = "pallet"


class TipoVC(str, Enum):
    """Types of Verifiable Credentials emitted."""

    VC_ORDEM_TRANSPORTE = "VC-OrdemTransporte"
    VC_COMPROVANTE_ENTREGA = "VC-ComprovanteEntrega"
    VC_EVENTO_LOGISTICO = "VC-EventoLogistico"


class EventoAuditoria(str, Enum):
    """Audit event types."""

    ORDEM_CRIADA = "ordem_criada"
    ORDEM_ACEITA = "ordem_aceita"
    DOCUMENTO_BAIXADO = "documento_baixado"
    ENTREGA_ASSINADA = "entrega_assinada"
    EMISSAO_VC = "emissao_vc"
    ATUALIZACAO_STATUS = "atualizacao_status"


VALIDADE_ORDEM_DIAS = 15
ISSUER_ID = "https://logistica.demo/issuers/transportadora"


