"""Application configuration management.

Loads settings from YAML files with environment variable substitution.
Follows 12-factor app principles: config in environment, not code.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database connection settings."""

    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False


class RedisConfig(BaseSettings):
    """Redis connection settings."""

    host: str = "redis"
    port: int = 6379
    db: int = 0
    password: str = ""
    decode_responses: bool = True


class QueueConfig(BaseSettings):
    """Celery / task queue settings."""

    broker_url: str = "redis://redis:6379/0"
    result_backend: str = "redis://redis:6379/0"
    task_serializer: str = "json"
    accept_content: list[str] = Field(default_factory=lambda: ["json"])
    result_serializer: str = "json"
    timezone: str = "America/Sao_Paulo"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 300
    worker_prefetch_multiplier: int = 1
    task_always_eager: bool = False
    task_store_eager_result: bool = False


class CryptoConfig(BaseSettings):
    """Cryptographic settings."""

    cert_path: str = "/secrets/cert.pem"
    key_path: str = "/secrets/key.pem"
    hsm_enabled: bool = False
    hsm_library_path: str = ""
    hsm_slot: int = 0
    hsm_pin: str = ""
    ecdsa_curve: str = "P-256"
    cryptosuite: str = "ecdsa-rdfc-2019"


class NotificationConfig(BaseSettings):
    """Push notification settings."""

    push_provider: str = "firebase"
    firebase_credentials: str = ""
    max_retries: int = 3
    retry_delay: float = 5.0


class SecurityConfig(BaseSettings):
    """Security settings."""

    mtls_enabled: bool = False
    ca_cert_path: str = "/secrets/ca.pem"
    jwt_algorithm: str = "ES256"
    jwt_issuer: str = "cargotrack-vc"
    jwt_audience: str = "cargotrack-clients"
    jwt_expiration_minutes: int = 60


class LogisticsConfig(BaseSettings):
    """Cargo tracking business settings."""

    validade_ordem_dias: int = 15
    descricao_padrao: str = "Carga geral"
    unidade: str = "kg"


class AppConfig(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="DTE_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    name: str = "cargotrack-vc"
    version: str = "1.0.0"
    debug: bool = False
    env: str = "production"


class ServerConfig(BaseSettings):
    """Server settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    timeout_keep_alive: int = 30


class APIConfig(BaseSettings):
    """API settings."""

    prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"


class LoggingConfig(BaseSettings):
    """Logging settings."""

    level: str = "INFO"
    format: str = "json"
    access_log: bool = True


class Settings(BaseSettings):
    """Root settings container."""

    model_config = SettingsConfigDict(
        env_prefix="DTE_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    database: DatabaseConfig = Field(default_factory=lambda: DatabaseConfig(url=""))
    redis: RedisConfig = Field(default_factory=RedisConfig)
    queue: QueueConfig = Field(default_factory=QueueConfig)
    crypto: CryptoConfig = Field(default_factory=CryptoConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logistics: LogisticsConfig = Field(default_factory=LogisticsConfig)


def _substitute_env_vars(value: Any) -> Any:
    """Recursively substitute ${VAR:default} patterns in config values."""
    if isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    if isinstance(value, str):
        pattern = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2) or ""
            return os.environ.get(var_name, default)

        return pattern.sub(replacer, value)
    return value


def load_settings(config_path: str | None = None) -> Settings:
    """Load settings from YAML file with environment substitution.

    Args:
        config_path: Path to YAML config file. If None, uses DTE_CONFIG_PATH env var
                     or defaults to config/settings.yaml.

    Returns:
        Populated Settings instance.
    """
    if config_path is None:
        config_path = os.environ.get("DTE_CONFIG_PATH", "config/settings.yaml")

    path = Path(config_path)
    if not path.exists():
        # Fallback to environment variables only
        return Settings()

    with open(path, encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    config = _substitute_env_vars(raw_config)
    return Settings(**config)


# Global settings instance (lazy-loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None


