"""Unit tests for VCRepository."""

from __future__ import annotations

from uuid import uuid4

from dte_mvp.repositories.vc_repository import VCRepository


def test_get_next_delivery_sequencial_returns_one_when_no_existing_records(db_session):
    repo = VCRepository(db_session)

    assert repo.get_next_delivery_sequencial("26") == 1


def test_get_next_delivery_sequencial_returns_next_value(db_session):
    repo = VCRepository(db_session)
    repo.save(
        "https://logistica.demo/vc/comprovante-entrega/26-000001",
        "VC-ComprovanteEntrega",
        str(uuid4()),
        "hash1",
        validade=None,
        vc_metadata={"document": {}},
    )
    repo.save(
        "https://logistica.demo/vc/comprovante-entrega/26-000005",
        "VC-ComprovanteEntrega",
        str(uuid4()),
        "hash2",
        validade=None,
        vc_metadata={"document": {}},
    )
    db_session.commit()

    assert repo.get_next_delivery_sequencial("26") == 6


