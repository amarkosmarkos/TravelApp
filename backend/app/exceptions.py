from fastapi import HTTPException, status
from typing import Any, Dict, Optional

class TravelAppException(HTTPException):
    """Excepción base para la aplicación"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class AuthenticationError(TravelAppException):
    """Error de autenticación"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(TravelAppException):
    """Error de autorización"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ValidationError(TravelAppException):
    """Error de validación"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

class NotFoundError(TravelAppException):
    """Error de recurso no encontrado"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class DatabaseError(TravelAppException):
    """Error de base de datos"""
    def __init__(self, detail: str = "Database error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class RateLimitError(TravelAppException):
    """Error de límite de tasa"""
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )

class ServiceUnavailableError(TravelAppException):
    """Error de servicio no disponible"""
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        ) 