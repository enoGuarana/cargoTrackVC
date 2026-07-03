"""ICP-Brasil ECDSA signer for Verifiable Credentials.

Implements W3C Data Integrity with ecdsa-rdfc-2019 cryptosuite.
Supports both file-based keys (dev/test) and HSM (production).
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA,
    EllipticCurvePrivateKey,
)

from dte_mvp.core.exceptions import CryptoError
from dte_mvp.infra.config import get_settings


class ICPBrasilSigner:
    """Signs Verifiable Credentials using ICP-Brasil certificates."""

    def __init__(self) -> None:
        self._private_key: EllipticCurvePrivateKey | None = None
        self._certificate: x509.Certificate | None = None
        self._cert_chain: list[x509.Certificate] = []
        self._verification_method: str = ""
        self._init_key()

    def _init_key(self) -> None:
        """Initialize signing key from file or HSM."""
        settings = get_settings()
        crypto_cfg = settings.crypto

        if crypto_cfg.hsm_enabled:
            self._init_hsm(crypto_cfg)
        else:
            self._init_file_key(crypto_cfg)

    def _init_file_key(self, crypto_cfg: Any) -> None:
        """Load key and certificate from PEM files."""
        try:
            key_path = Path(crypto_cfg.key_path)
            cert_path = Path(crypto_cfg.cert_path)

            if not key_path.exists():
                raise CryptoError(f"Key file not found: {key_path}")
            if not cert_path.exists():
                raise CryptoError(f"Certificate file not found: {cert_path}")

            with open(key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )

            with open(cert_path, "rb") as f:
                self._certificate = x509.load_pem_x509_certificate(f.read())

            # Build verification method URI from certificate subject
            cn = self._certificate.subject.get_attributes_for_oid(
                x509.NameOID.COMMON_NAME
            )[0].value
            self._verification_method = f"https://transportes.gov.br/issuers/mt#{cn}"

        except Exception as e:
            raise CryptoError(f"Failed to load signing key: {e}") from e

    def _init_hsm(self, crypto_cfg: Any) -> None:
        """Initialize HSM connection (placeholder for production)."""
        # In production, this would use PKCS#11 to connect to HSM
        # and perform signing operations without exposing the private key
        raise CryptoError("HSM support not yet implemented")

    def _canonicalize_document(self, document: dict[str, Any]) -> bytes:
        """Canonicalize JSON-LD document for signing.

        For MVP: simplified canonicalization using deterministic JSON serialization.
        Production should use RDF Dataset Canonicalization (RDF-CANON).
        """
        # Deterministic JSON serialization (keys sorted, no extra whitespace)
        canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return canonical.encode("utf-8")

    def _hash_document(self, canonical_doc: bytes) -> bytes:
        """Hash canonicalized document using SHA-256 (for P-256 curve)."""
        return hashlib.sha256(canonical_doc).digest()

    def _create_proof_config(
        self,
        document_id: str,
        created: datetime,
    ) -> dict[str, Any]:
        """Create the proof configuration block."""
        return {
            "type": "DataIntegrityProof",
            "cryptosuite": "ecdsa-rdfc-2019",
            "created": created.isoformat().replace("+00:00", "Z"),
            "verificationMethod": self._verification_method,
            "proofPurpose": "assertionMethod",
            "@context": ["https://www.w3.org/ns/credentials/v2"],
        }

    def sign_vc(
        self,
        vc_document: dict[str, Any],
        document_id: str,
    ) -> dict[str, Any]:
        """Sign a Verifiable Credential document.

        Args:
            vc_document: The VC payload (without proof).
            document_id: Unique identifier for the VC.

        Returns:
            The VC document with proof block attached.

        Raises:
            CryptoError: If signing fails.
        """
        if self._private_key is None:
            raise CryptoError("Signing key not initialized")

        try:
            created = datetime.now(UTC)

            # Create proof configuration
            proof_config = self._create_proof_config(document_id, created)

            # Canonicalize and hash the document
            canonical_doc = self._canonicalize_document(vc_document)
            doc_hash = self._hash_document(canonical_doc)

            # Canonicalize and hash proof config
            canonical_config = self._canonicalize_document(proof_config)
            config_hash = self._hash_document(canonical_config)

            # Combine hashes (concatenate)
            combined_hash = doc_hash + config_hash

            # Sign with ECDSA
            signature = self._private_key.sign(
                combined_hash,
                ECDSA(hashes.SHA256()),
            )

            # Encode signature as base58btc multibase
            proof_value = "z" + base64.b64encode(signature).decode("ascii")

            # Attach proof to document
            proof_block = {
                "type": "DataIntegrityProof",
                "cryptosuite": "ecdsa-rdfc-2019",
                "created": created.isoformat().replace("+00:00", "Z"),
                "verificationMethod": self._verification_method,
                "proofPurpose": "assertionMethod",
                "proofValue": proof_value,
            }

            signed_doc = dict(vc_document)
            signed_doc["proof"] = proof_block
            return signed_doc

        except Exception as e:
            raise CryptoError(f"Failed to sign VC: {e}") from e

    def verify_vc(
        self,
        signed_vc: dict[str, Any],
        public_key_pem: str | bytes | None = None,
    ) -> bool:
        """Verify the signature of a Verifiable Credential.

        Args:
            signed_vc: The signed VC document containing the proof.
            public_key_pem: Optional public key in PEM format to verify against.
                If not provided, uses the internal public key.

        Returns:
            True if signature is valid, False otherwise.
            
        Raises:
            CryptoError: If the VC is malformed or missing proof.
        """
        try:
            from cryptography.exceptions import InvalidSignature
            
            if "proof" not in signed_vc:
                raise CryptoError("VC is missing proof block")
                
            proof = signed_vc["proof"]
            if "proofValue" not in proof:
                raise CryptoError("Proof is missing proofValue")
                
            # Extract signature
            proof_value = proof["proofValue"]
            if not proof_value.startswith("z"):
                raise CryptoError("Invalid proofValue format")
            
            signature = base64.b64decode(proof_value[1:])
            
            # Reconstruct document without proof
            vc_document = dict(signed_vc)
            del vc_document["proof"]
            
            # Canonicalize and hash document
            canonical_doc = self._canonicalize_document(vc_document)
            doc_hash = self._hash_document(canonical_doc)
            
            # Reconstruct proof config
            proof_config = dict(proof)
            del proof_config["proofValue"]
            proof_config["@context"] = ["https://www.w3.org/ns/credentials/v2"]
            
            canonical_config = self._canonicalize_document(proof_config)
            config_hash = self._hash_document(canonical_config)
            
            combined_hash = doc_hash + config_hash
            
            # Get public key
            if public_key_pem:
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode() if isinstance(public_key_pem, str) else public_key_pem
                )
            elif self._private_key:
                public_key = self._private_key.public_key()
            elif self._certificate:
                public_key = self._certificate.public_key()
            else:
                raise CryptoError("No public key available for verification")
                
            public_key.verify(
                signature,
                combined_hash,
                ECDSA(hashes.SHA256())
            )
            return True
            
        except InvalidSignature:
            return False
        except Exception as e:
            if isinstance(e, CryptoError):
                raise
            raise CryptoError(f"Failed to verify VC: {e}") from e

    def get_public_key_pem(self) -> str:
        """Get the public key in PEM format for verifier cache."""
        if self._certificate is None:
            raise CryptoError("Certificate not loaded")
        return self._certificate.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode("ascii")

    def get_certificate_chain(self) -> list[str]:
        """Get the certificate chain for offline verification."""
        if self._certificate is None:
            raise CryptoError("Certificate not loaded")
        return [
            cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
            for cert in [self._certificate] + self._cert_chain
        ]


# Singleton instance
_signer: ICPBrasilSigner | None = None


def get_signer() -> ICPBrasilSigner:
    """Get the global signer instance."""
    global _signer
    if _signer is None:
        _signer = ICPBrasilSigner()
    return _signer


