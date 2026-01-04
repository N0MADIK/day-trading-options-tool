from typing import Any, Dict, Optional


class BaseDomainError(Exception):
    """Base exception for all domain errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(BaseDomainError):
    """Resource not found error"""
    pass


class ConflictError(BaseDomainError):
    """Resource conflict error (e.g., duplicate)"""
    pass


class ValidationError(BaseDomainError):
    """Validation error"""
    pass


class UnauthorizedError(BaseDomainError):
    """Unauthorized access error"""
    pass


class ForbiddenError(BaseDomainError):
    """Forbidden access error"""
    pass


class ExternalServiceError(BaseDomainError):
    """External service error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class DatabaseError(BaseDomainError):
    """Database operation error"""
    pass
