"""Unit tests for the cargo tracking lifecycle service."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from dte_mvp.core.constants import StatusOperacao
from dte_mvp.models.ordem import AssinaturaEntregaEntrada, OrdemTransporte, OrdemTransporteEntrada
from dte_mvp.services.ordem_service import OrdemService


@pytest.fixture(autouse=True)
def mock_signer(monkeypatch, test_key_pair):
    """Mock signer for all tests in this module."""
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


@pytest.mark.asyncio
async def test_criar_ordem_success(sample_ordem, db_session):
    service = OrdemService()

    result = await service.criar_ordem(sample_ordem)

    assert result.is_success
    ordem = result.value
    assert isinstance(ordem, OrdemTransporte)
    assert ordem.numero_ordem == sample_ordem.numero_ordem
    assert ordem.status == StatusOperacao.CRIADA
    assert ordem.chave_ordem == sample_ordem.chave_ordem


@pytest.mark.asyncio
async def test_criar_ordem_idempotency(sample_ordem, db_session):
    service = OrdemService()

    result1 = await service.criar_ordem(sample_ordem)
    result2 = await service.criar_ordem(sample_ordem)

    assert result1.is_success
    assert result2.is_success
    assert result1.value.id == result2.value.id


@pytest.mark.asyncio
async def test_fluxo_aceite_download_e_entrega(sample_ordem, db_session):
    service = OrdemService()

    created = await service.criar_ordem(sample_ordem)
    ordem_id = created.value.id

    accepted = await service.aceitar_ordem(ordem_id)
    assert accepted.is_success
    assert accepted.value["status"] == "aceita"

    document = await service.entregar_documento_motorista(ordem_id, sample_ordem.cpf_motorista)
    assert document.is_success
    assert document.value["verifiableCredential"]

    delivery = await service.assinar_entrega(
        ordem_id,
        AssinaturaEntregaEntrada(
            recebedor_nome="Bruno Recebedor",
            documento_recebedor="1234567",
        ),
    )
    assert delivery.is_success
    assert delivery.value["status"] == "entregue"
    assert delivery.value["vc_comprovante_id"]


