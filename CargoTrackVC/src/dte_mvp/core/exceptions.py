"""Domain exceptions for the cargo tracking MVP system."""


class CargoTrackError(Exception):
    """Base exception for CargoTrack domain errors."""

    def __init__(self, message: str, code: str = "CARGOTRACK_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(CargoTrackError):
    """Raised when business rule validation fails."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message, code)


class IdempotencyError(CargoTrackError):
    """Raised when an order has already been processed."""

    def __init__(self, message: str, ordem_id: str | None = None) -> None:
        self.ordem_id = ordem_id
        super().__init__(message, "IDEMPOTENCY_ERROR")


class ExternalAPIError(CargoTrackError):
    """Raised when an external API call fails after retries."""

    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: int | None = None,
        retry_exhausted: bool = True,
    ) -> None:
        self.api_name = api_name
        self.status_code = status_code
        self.retry_exhausted = retry_exhausted
        super().__init__(message, "EXTERNAL_API_ERROR")


class CryptoError(CargoTrackError):
    """Raised when cryptographic operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "CRYPTO_ERROR")


class NotificationError(CargoTrackError):
    """Raised when push notification fails."""

    def __init__(self, message: str, recipient: str | None = None) -> None:
        self.recipient = recipient
        super().__init__(message, "NOTIFICATION_ERROR")


class NotFoundError(CargoTrackError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, resource_type: str = "resource") -> None:
        self.resource_type = resource_type
        super().__init__(message, "NOT_FOUND")



