from typing import Any


class DomainError(Exception):
    code = "domain_error"
    status_code = 400

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ResourceNotFoundError(DomainError):
    code = "resource_not_found"
    status_code = 404


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class AuthenticationError(DomainError):
    code = "authentication_failed"
    status_code = 401


class AuthorizationError(DomainError):
    code = "permission_denied"
    status_code = 403


class InvalidTransitionError(ConflictError):
    code = "invalid_state_transition"

