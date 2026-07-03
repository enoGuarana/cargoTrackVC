"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

# Set test config before importing app
os.environ["DTE_CONFIG_PATH"] = "config/settings.test.yaml"

from datetime import UTC

from dte_mvp.infra.config import load_settings, reset_settings
from dte_mvp.infra.database.session import get_engine
from dte_mvp.main import create_app


@pytest.fixture(scope="session")
def test_settings():
    """Load test settings."""
    reset_settings()
    return load_settings("config/settings.test.yaml")


@pytest.fixture(scope="function")
def db_session():
    """Provide a fresh database session for each test."""
    from sqlalchemy.orm import sessionmaker

    from dte_mvp.infra.database.models import Base

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provide a FastAPI test client."""
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def test_key_pair():
    """Generate test ECDSA key pair."""
    private_key = ec.generate_private_key(ec.SECP256R1())

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Create self-signed certificate for testing
    from datetime import datetime, timedelta

    from cryptography import x509
    from cryptography.x509.oid import NameOID

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Ministerio dos Transportes"),
        x509.NameAttribute(NameOID.COMMON_NAME, "cargotrack-test"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC))
        .not_valid_after(datetime.now(UTC) + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)

    os.makedirs("tests/fixtures", exist_ok=True)
    key_path = "tests/fixtures/test_key.pem"
    cert_path = "tests/fixtures/test_cert.pem"

    with open(key_path, "wb") as f:
        f.write(private_pem)

    with open(cert_path, "wb") as f:
        f.write(cert_pem)

    yield {
        "private_key": private_key,
        "public_key": public_key,
        "private_pem": private_pem,
        "public_pem": public_pem,
        "cert_pem": cert_pem,
        "key_path": key_path,
        "cert_path": cert_path,
    }


