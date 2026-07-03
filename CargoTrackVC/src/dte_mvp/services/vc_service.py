"""Verifiable Credential generation and signing service."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from dte_mvp.core.constants import ISSUER_ID, VALIDADE_ORDEM_DIAS, StatusOperacao
from dte_mvp.infra.crypto.signer import get_signer
from dte_mvp.models.ordem import AssinaturaEntregaEntrada, OrdemTransporteEntrada

logger = structlog.get_logger()


class VCService:
    """Service for generating and signing Verifiable Credentials."""

    def __init__(self) -> None:
        self._signer = get_signer()

    def gerar_vc_ordem_transporte(
        self,
        ordem: OrdemTransporteEntrada,
        ordem_id: UUID,
    ) -> dict[str, Any]:
        """Generate the credential delivered to the driver after carrier acceptance."""
        vc_id = f"https://logistica.demo/vc/ordem-transporte/{ordem_id}"
        valid_from = datetime.now(UTC)
        valid_until = valid_from + timedelta(days=VALIDADE_ORDEM_DIAS)

        vc_document = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://logistica.demo/contexts/cargo-tracking/v1",
            ],
            "id": vc_id,
            "type": ["VerifiableCredential", "TransportOrderCredential"],
            "issuer": ISSUER_ID,
            "validFrom": valid_from.isoformat().replace("+00:00", "Z"),
            "validUntil": valid_until.isoformat().replace("+00:00", "Z"),
            "credentialSubject": {
                "id": f"urn:uuid:{ordem_id}",
                "idOrdem": str(ordem_id),
                "numeroOrdem": ordem.numero_ordem,
                "origem": ordem.origem,
                "destino": ordem.destino,
                "descricaoCarga": ordem.descricao_carga,
                "quantidade": ordem.quantidade,
                "unidade": ordem.unidade,
                "valorFrete": ordem.valor_frete,
                "placa": ordem.placa,
                "motoristaNome": ordem.motorista_nome,
                "motoristaCPF": ordem.cpf_motorista,
                "embarcador": ordem.embarcador,
                "transportadora": ordem.transportadora,
                "recebedor": ordem.recebedor,
                "status": StatusOperacao.ACEITA.value,
            },
        }

        signed = self._signer.sign_vc(vc_document, vc_id)
        logger.info("vc.ordem_transporte.generated", ordem_id=str(ordem_id))
        return signed

    def gerar_vc_evento_logistico(
        self,
        ordem_id: UUID,
        evento: str,
        ator: str,
        situacao: str,
    ) -> dict[str, Any]:
        """Generate a small credential for an auditable logistics event."""
        now = datetime.now(UTC)
        vc_id = f"https://logistica.demo/vc/evento/{ordem_id}/{evento}/{int(now.timestamp())}"
        vc_document = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://logistica.demo/contexts/cargo-tracking/v1",
            ],
            "id": vc_id,
            "type": ["VerifiableCredential", "LogisticsEventCredential"],
            "issuer": ISSUER_ID,
            "validFrom": now.isoformat().replace("+00:00", "Z"),
            "credentialSubject": {
                "id": f"urn:uuid:{ordem_id}",
                "evento": evento,
                "ator": ator,
                "dataEvento": now.isoformat().replace("+00:00", "Z"),
                "situacao": situacao,
            },
        }
        return self._signer.sign_vc(vc_document, vc_id)

    def gerar_vc_comprovante_entrega(
        self,
        ordem: OrdemTransporteEntrada,
        ordem_id: UUID,
        assinatura: AssinaturaEntregaEntrada,
    ) -> dict[str, Any]:
        """Generate the final proof-of-delivery credential."""
        now = datetime.now(UTC)
        vc_id = f"https://logistica.demo/vc/comprovante-entrega/{ordem_id}"
        vc_document = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://logistica.demo/contexts/cargo-tracking/v1",
            ],
            "id": vc_id,
            "type": ["VerifiableCredential", "ProofOfDeliveryCredential"],
            "issuer": ISSUER_ID,
            "validFrom": now.isoformat().replace("+00:00", "Z"),
            "credentialSubject": {
                "id": f"urn:uuid:{ordem_id}",
                "idOrdem": str(ordem_id),
                "numeroOrdem": ordem.numero_ordem,
                "origem": ordem.origem,
                "destino": ordem.destino,
                "descricaoCarga": ordem.descricao_carga,
                "transportadora": ordem.transportadora,
                "motoristaCPF": ordem.cpf_motorista,
                "recebedor": ordem.recebedor,
                "recebedorNome": assinatura.recebedor_nome,
                "documentoRecebedor": assinatura.documento_recebedor,
                "entregueEm": now.isoformat().replace("+00:00", "Z"),
                "localizacao": {
                    "latitude": assinatura.latitude,
                    "longitude": assinatura.longitude,
                },
                "observacao": assinatura.observacao,
                "status": StatusOperacao.ENTREGUE.value,
            },
        }
        signed = self._signer.sign_vc(vc_document, vc_id)
        logger.info("vc.comprovante_entrega.generated", ordem_id=str(ordem_id))
        return signed

    def calcular_hash(self, vc_document: dict[str, Any]) -> str:
        """Calculate SHA-256 hash of a VC for registry."""
        canonical = json.dumps(vc_document, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


