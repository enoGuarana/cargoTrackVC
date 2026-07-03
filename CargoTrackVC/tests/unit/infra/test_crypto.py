"""Unit tests for cryptographic operations."""

from __future__ import annotations

from datetime import UTC, datetime

from dte_mvp.infra.crypto.signer import ICPBrasilSigner


class TestICPBrasilSigner:
    """Tests for ICP-Brasil signer."""

    def test_sign_vc_creates_valid_structure(self, test_key_pair):
        """Test signing produces valid VC structure."""
        # Mock the signer to use test keys
        signer = ICPBrasilSigner.__new__(ICPBrasilSigner)
        signer._private_key = test_key_pair["private_key"]
        signer._certificate = None  # Will be set from test cert
        signer._cert_chain = []
        signer._verification_method = "https://transportes.gov.br/issuers/mt#test"

        doc = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "urn:uuid:test",
            "type": ["VerifiableCredential"],
            "issuer": "https://transportes.gov.br/issuers/mt",
            "validFrom": datetime.now(UTC).isoformat(),
            "credentialSubject": {"id": "urn:uuid:subject"},
        }

        result = signer.sign_vc(doc, "urn:uuid:test")

        assert "proof" in result
        proof = result["proof"]
        assert proof["type"] == "DataIntegrityProof"
        assert proof["cryptosuite"] == "ecdsa-rdfc-2019"
        assert proof["proofPurpose"] == "assertionMethod"
        assert proof["verificationMethod"] == signer._verification_method
        assert "proofValue" in proof
        assert proof["proofValue"].startswith("z")  # base58btc multibase prefix

    def test_sign_vc_deterministic_canonicalization(self, test_key_pair):
        """Test canonicalization is deterministic."""
        signer = ICPBrasilSigner.__new__(ICPBrasilSigner)
        signer._private_key = test_key_pair["private_key"]
        signer._certificate = None
        signer._cert_chain = []
        signer._verification_method = "https://transportes.gov.br/issuers/mt#test"

        # Same document with different key order
        doc1 = {"a": 1, "b": 2, "c": 3}
        doc2 = {"c": 3, "a": 1, "b": 2}

        canonical1 = signer._canonicalize_document(doc1)
        canonical2 = signer._canonicalize_document(doc2)

        assert canonical1 == canonical2

    def test_hash_document(self):
        """Test document hashing."""
        signer = ICPBrasilSigner.__new__(ICPBrasilSigner)

        doc = b"test document"
        hash1 = signer._hash_document(doc)
        hash2 = signer._hash_document(doc)

        assert hash1 == hash2
        assert len(hash1) == 32  # SHA-256 produces 32 bytes

    def test_verify_vc_success(self, test_key_pair):
        """Test successful verification of a signed VC."""
        signer = ICPBrasilSigner.__new__(ICPBrasilSigner)
        signer._private_key = test_key_pair["private_key"]
        signer._certificate = None
        signer._cert_chain = []
        signer._verification_method = "https://transportes.gov.br/issuers/mt#test"

        doc = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "urn:uuid:test",
            "type": ["VerifiableCredential"],
            "issuer": "https://transportes.gov.br/issuers/mt",
            "validFrom": datetime.now(UTC).isoformat(),
            "credentialSubject": {"id": "urn:uuid:subject"},
        }

        signed_vc = signer.sign_vc(doc, "urn:uuid:test")
        
        # Verify with internal key
        assert signer.verify_vc(signed_vc) is True
        
        # Verify with explicit public key PEM
        assert signer.verify_vc(signed_vc, test_key_pair["public_pem"]) is True

    def test_verify_vc_failure_tampered_doc(self, test_key_pair):
        """Test verification fails if document is tampered."""
        signer = ICPBrasilSigner.__new__(ICPBrasilSigner)
        signer._private_key = test_key_pair["private_key"]
        signer._certificate = None
        signer._cert_chain = []
        signer._verification_method = "https://transportes.gov.br/issuers/mt#test"

        doc = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "urn:uuid:test",
            "type": ["VerifiableCredential"],
            "issuer": "https://transportes.gov.br/issuers/mt",
            "validFrom": datetime.now(UTC).isoformat(),
            "credentialSubject": {"id": "urn:uuid:subject"},
        }

        signed_vc = signer.sign_vc(doc, "urn:uuid:test")
        
        # Tamper with the document
        signed_vc["credentialSubject"]["id"] = "urn:uuid:hacked"
        
        assert signer.verify_vc(signed_vc) is False


