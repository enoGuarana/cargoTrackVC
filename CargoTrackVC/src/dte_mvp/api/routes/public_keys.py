"""Public key cache endpoint for proof-of-delivery verifier apps."""

from __future__ import annotations

from fastapi import APIRouter

from dte_mvp.infra.crypto.signer import get_signer

router = APIRouter(prefix="/public-keys", tags=["Public Keys"])


@router.get("", summary="Cache de chaves publicas do emissor")
async def get_public_keys() -> dict:
    """Download public key cache for offline verification.

    The verifier app should periodically call this endpoint
    to update its local cache of issuer public keys.
    """
    signer = get_signer()
    return {
        "keys": [
            {
                "verificationMethod": signer._verification_method,
                "publicKeyPem": signer.get_public_key_pem(),
                "certificateChain": signer.get_certificate_chain(),
                "updated_at": "2026-07-02T00:00:00Z",
            }
        ],
        "algorithm": "ECDSA",
        "curve": "P-256",
        "cryptosuite": "ecdsa-rdfc-2019",
    }



