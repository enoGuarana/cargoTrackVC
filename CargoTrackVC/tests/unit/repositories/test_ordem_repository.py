from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from dte_mvp.core.constants import StatusOperacao
from dte_mvp.infra.database.models import OrdemORM
from dte_mvp.repositories.ordem_repository import OrdemRepository


def test_get_active_by_motorista_hash_returns_matching_record(db_session):
    cpf = "12345678901"
    cpf_hash = sha256(cpf.encode()).hexdigest()[:16]

    ordem_id = str(uuid4())
    ordem = OrdemORM(
        id=ordem_id,
        numero_ordem="OT-2026-0001",
        chave_ordem="SHIP-2026-0001",
        status=StatusOperacao.ACEITA.value,
        hash_ordem="deadbeef",
        participantes_minimizados={"cpf_motorista_hash": cpf_hash},
        ordem_payload={"origem": "Rondonopolis/MT", "destino": "Santos/SP"},
    )

    db_session.add(ordem)
    db_session.commit()

    repo = OrdemRepository(db_session)
    results = repo.get_active_by_motorista_hash(cpf_hash)

    assert len(results) == 1
    assert results[0].id == ordem_id
    assert results[0].participantes_minimizados["cpf_motorista_hash"] == cpf_hash


def test_get_active_by_motorista_hash_skips_finished_records(db_session):
    cpf = "12345678901"
    cpf_hash = sha256(cpf.encode()).hexdigest()[:16]

    ordem = OrdemORM(
        id=str(uuid4()),
        numero_ordem="OT-2026-0002",
        chave_ordem="SHIP-2026-0002",
        status=StatusOperacao.ENTREGUE.value,
        hash_ordem="deadbeef",
        participantes_minimizados={"cpf_motorista_hash": cpf_hash},
        ordem_payload={"origem": "Rondonopolis/MT", "destino": "Santos/SP"},
    )

    db_session.add(ordem)
    db_session.commit()

    repo = OrdemRepository(db_session)
    assert repo.get_active_by_motorista_hash(cpf_hash) == []


