"""Custom exceptions for Veriqko."""

from typing import Any


class VeriqkoError(Exception):
    """Base class for all Veriqko exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class StorageError(VeriqkoError):
    """Exception raised for storage-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="STORAGE_ERROR",
            details=details,
        )


class ValidationError(VeriqkoError):
    """Exception raised for validation failures."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(VeriqkoError):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )
