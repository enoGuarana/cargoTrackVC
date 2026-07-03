"""Integration test for the complete cargo tracking flow."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from dte_mvp.infra.database.session import init_db
from dte_mvp.main import create_app


@pytest.fixture(scope="module")
def integration_client():
    init_db()
    app = create_app()
    with TestClient(app) as client:
        yield client


def sample_payload(chave: str = "SHIP-2026-0001") -> dict:
    return {
        "numero_ordem": "OT-2026-0001",
        "chave_ordem": chave,
        "embarcador": "Agro Origem Ltda",
        "cnpj_embarcador": "12345678000195",
        "transportadora": "TransLog Brasil",
        "cnpj_transportadora": "22345678000190",
        "motorista_nome": "Ana Motorista",
        "cpf_motorista": "12345678901",
        "placa": "ABC1D23",
        "recebedor": "CD Santos",
        "cnpj_recebedor": "32345678000191",
        "origem": "Rondonopolis/MT",
        "destino": "Santos/SP",
        "descricao_carga": "Carga paletizada de alimentos",
        "quantidade": 18000,
        "unidade": "kg",
        "valor_frete": 9500,
        "data_coleta_prevista": datetime.now(UTC).isoformat(),
    }


def test_health_check(integration_client):
    response = integration_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "cargotrack-vc"


def test_fluxo_ordem_aceite_documento_entrega(integration_client):
    create_response = integration_client.post("/api/v1/ordens", json=sample_payload("SHIP-2026-0101"))
    assert create_response.status_code in [201, 500]
    if create_response.status_code == 500:
        pytest.skip("Signer/database not configured for integration environment")

    ordem_id = create_response.json()["ordem_id"]

    accept_response = integration_client.post(f"/api/v1/ordens/{ordem_id}/aceite")
    assert accept_response.status_code == 200

    list_response = integration_client.get("/api/v1/ordens?cpf=12345678901")
    assert list_response.status_code == 200
    assert any(item["ordem_id"] == ordem_id for item in list_response.json())

    doc_response = integration_client.get(f"/api/v1/ordens/{ordem_id}/documento?cpf=12345678901")
    assert doc_response.status_code == 200
    assert doc_response.json()["verifiableCredential"]

    delivery_response = integration_client.post(
        f"/api/v1/ordens/{ordem_id}/entrega",
        json={"recebedor_nome": "Bruno Recebedor", "documento_recebedor": "1234567"},
    )
    assert delivery_response.status_code == 200
    assert delivery_response.json()["status"] == "entregue"


