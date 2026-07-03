"""VC registry repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from dte_mvp.infra.database.models import VCRegistryORM


class VCRepository:
    """Repository for Verifiable Credential registry (hash only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, vc_id: str, tipo: str, dte_id: str | None, hash_vc: str, validade: Any = None, vc_metadata: dict | None = None) -> VCRegistryORM:
        """Save VC hash to registry."""
        # If the VC ID already exists in the registry, return it (idempotent)
        existing = self.get_by_id(vc_id)
        if existing:
            return existing

        orm = VCRegistryORM(
            id=vc_id,
            tipo=tipo,
            dte_id=dte_id,
            hash_vc=hash_vc,
            validade=validade,
            vc_metadata=vc_metadata or {},
        )
        self._session.add(orm)
        self._session.flush()
        return orm

    def get_next_delivery_sequencial(self, ano: str) -> int:
        """Get the next sequential number for proof-of-delivery credentials."""
        prefix = f"https://logistica.demo/vc/comprovante-entrega/{ano}-"
        stmt = select(VCRegistryORM.id).where(VCRegistryORM.id.startswith(prefix))
        existing_ids = [vc_id for vc_id in self._session.execute(stmt).scalars().all() if vc_id]

        max_sequencial = 0
        for vc_id in existing_ids:
            try:
                sequencial = int(vc_id.rsplit("-", 1)[-1])
            except ValueError:
                continue
            max_sequencial = max(max_sequencial, sequencial)

        return max_sequencial + 1

    def get_by_id(self, vc_id: str) -> VCRegistryORM | None:
        """Get VC registry entry by ID."""
        return self._session.get(VCRegistryORM, vc_id)

    def get_by_dte(self, dte_id: UUID) -> list[VCRegistryORM]:
        """Get all VCs for a transport order."""
        stmt = select(VCRegistryORM).where(VCRegistryORM.dte_id == str(dte_id))
        return list(self._session.execute(stmt).scalars().all())


