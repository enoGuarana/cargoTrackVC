"""Unit tests for VCService in the cargo tracking MVP."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dte_mvp.core.constants import VALIDADE_ORDEM_DIAS
from dte_mvp.models.ordem import AssinaturaEntregaEntrada, OrdemTransporteEntrada
from dte_mvp.services.vc_service import VCService


@pytest.fixture
def vc_service(monkeypatch, test_key_pair):
    """Create VCService instance with mocked signer."""
    from dte_mvp.infra.crypto.signer import ICPBrasilSigner

    mock_signer = ICPBrasilSigner.__new__(ICPBrasilSigner)
    mock_signer._private_key = test_key_pair["private_key"]
    mock_signer._certificate = None
    mock_signer._cert_chain = []
    mock_signer._verification_method = "https://logistica.demo/issuers/transportadora#test"

    def mock_get_signer():
        return mock_signer

    monkeypatch.setattr("dte_mvp.services.vc_service.get_signer", mock_get_signer)
    monkeypatch.setattr("dte_mvp.infra.crypto.signer.get_signer", mock_get_signer)

    return VCService()


@pytest.fixture
def sample_ordem():
    """Create sample transport order."""
    return OrdemTransporteEntrada(
        numero_ordem="OT-2026-0001",
        chave_ordem="SHIP-2026-0001",
        embarcador="Agro Origem Ltda",
        cnpj_embarcador="12345678000195",
        transportadora="TransLog Brasil",
        cnpj_transportadora="22345678000190",
        motorista_nome="Ana Motorista",
        cpf_motorista="12345678901",
        placa="ABC1D23",
        recebedor="CD Santos",
        cnpj_recebedor="32345678000191",
        origem="Rondonopolis/MT",
        destino="Santos/SP",
        descricao_carga="Carga paletizada de alimentos",
        quantidade=18000,
        unidade="kg",
        valor_frete=9500,
        data_coleta_prevista=datetime.now(UTC),
    )


def test_gerar_vc_ordem_transporte_success(vc_service, sample_ordem):
    ordem_id = uuid4()

    result = vc_service.gerar_vc_ordem_transporte(sample_ordem, ordem_id)

    assert result["type"] == ["VerifiableCredential", "TransportOrderCredential"]
    assert "proof" in result
    assert result["credentialSubject"]["idOrdem"] == str(ordem_id)
    assert result["credentialSubject"]["descricaoCarga"] == "Carga paletizada de alimentos"
    assert result["credentialSubject"]["status"] == "aceita"


def test_vc_ordem_validade(vc_service, sample_ordem):
    result = vc_service.gerar_vc_ordem_transporte(sample_ordem, uuid4())

    valid_from = datetime.fromisoformat(result["validFrom"].replace("Z", "+00:00"))
    valid_until = datetime.fromisoformat(result["validUntil"].replace("Z", "+00:00"))

    assert round((valid_until - valid_from).total_seconds() / 86400) == VALIDADE_ORDEM_DIAS


def test_gerar_vc_comprovante_entrega_success(vc_service, sample_ordem):
    ordem_id = uuid4()
    assinatura = AssinaturaEntregaEntrada(
        recebedor_nome="Bruno Recebedor",
        documento_recebedor="1234567",
        observacao="Carga recebida sem avarias.",
    )

    result = vc_service.gerar_vc_comprovante_entrega(sample_ordem, ordem_id, assinatura)

    assert result["type"] == ["VerifiableCredential", "ProofOfDeliveryCredential"]
    assert result["credentialSubject"]["idOrdem"] == str(ordem_id)
    assert result["credentialSubject"]["recebedorNome"] == "Bruno Recebedor"
    assert result["credentialSubject"]["status"] == "entregue"


def test_calcular_hash_deterministic(vc_service):
    doc = {"a": 1, "b": "test"}

    assert vc_service.calcular_hash(doc) == vc_service.calcular_hash(doc)
    assert len(vc_service.calcular_hash(doc)) == 64


