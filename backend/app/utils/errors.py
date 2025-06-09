from typing import Dict, Any, Optional
from fastapi import HTTPException, status
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Error base de la aplicación"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    """Error de validación"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )

class AuthenticationError(AppError):
    """Error de autenticación"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )

class AuthorizationError(AppError):
    """Error de autorización"""
    
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )

class NotFoundError(AppError):
    """Error de recurso no encontrado"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND_ERROR",
            details=details
        )

class ConflictError(AppError):
    """Error de conflicto"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details
        )

class DatabaseError(AppError):
    """Error de base de datos"""
    
    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )

class ExternalServiceError(AppError):
    """Error de servicio externo"""
    
    def __init__(
        self,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )

def handle_error(error: Exception) -> HTTPException:
    """
    Manejar error y convertirlo a HTTPException
    
    Args:
        error: Error a manejar
    
    Returns:
        HTTPException: Error HTTP
    """
    if isinstance(error, AppError):
        logger.error(f"Application error: {error.message}", extra={
            "error_code": error.error_code,
            "details": error.details
        })
        return HTTPException(
            status_code=error.status_code,
            detail={
                "message": error.message,
                "error_code": error.error_code,
                "details": error.details
            }
        )
    
    # Error no manejado
    logger.error(f"Unhandled error: {str(error)}", exc_info=True)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "message": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": {"error": str(error)} if settings.DEBUG else None
        }
    )

def raise_validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de validación
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise ValidationError(message=message, details=details)

def raise_authentication_error(message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de autenticación
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise AuthenticationError(message=message, details=details)

def raise_authorization_error(message: str = "Not authorized", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de autorización
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise AuthorizationError(message=message, details=details)

def raise_not_found_error(message: str = "Resource not found", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de recurso no encontrado
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise NotFoundError(message=message, details=details)

def raise_conflict_error(message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de conflicto
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise ConflictError(message=message, details=details)

def raise_database_error(message: str = "Database error", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de base de datos
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise DatabaseError(message=message, details=details)

def raise_external_service_error(message: str = "External service error", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Lanzar error de servicio externo
    
    Args:
        message: Mensaje de error
        details: Detalles del error
    """
    raise ExternalServiceError(message=message, details=details)

def handle_validation_error(error: ValidationError) -> HTTPException:
    """
    Manejar error de validación
    
    Args:
        error: Error de validación
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "Validation Error",
            "message": str(error),
            "code": "VALIDATION_ERROR"
        }
    )

def handle_authentication_error(error: AuthenticationError) -> HTTPException:
    """
    Manejar error de autenticación
    
    Args:
        error: Error de autenticación
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "Authentication Error",
            "message": str(error),
            "code": "AUTHENTICATION_ERROR"
        }
    )

def handle_authorization_error(error: AuthorizationError) -> HTTPException:
    """
    Manejar error de autorización
    
    Args:
        error: Error de autorización
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "Authorization Error",
            "message": str(error),
            "code": "AUTHORIZATION_ERROR"
        }
    )

def handle_not_found_error(message: str) -> HTTPException:
    """
    Manejar error de recurso no encontrado
    
    Args:
        message: Mensaje de error
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "Not Found",
            "message": message,
            "code": "NOT_FOUND"
        }
    )

def handle_conflict_error(message: str) -> HTTPException:
    """
    Manejar error de conflicto
    
    Args:
        message: Mensaje de error
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "error": "Conflict",
            "message": message,
            "code": "CONFLICT"
        }
    )

def handle_rate_limit_error(message: str) -> HTTPException:
    """
    Manejar error de límite de tasa
    
    Args:
        message: Mensaje de error
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate Limit Exceeded",
            "message": message,
            "code": "RATE_LIMIT_EXCEEDED"
        }
    )

def handle_internal_server_error(message: str) -> HTTPException:
    """
    Manejar error interno del servidor
    
    Args:
        message: Mensaje de error
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "Internal Server Error",
            "message": message,
            "code": "INTERNAL_SERVER_ERROR"
        }
    )

def handle_database_error(error: Exception) -> HTTPException:
    """
    Manejar error de base de datos
    
    Args:
        error: Error de base de datos
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "Database Error",
            "message": "An error occurred while accessing the database",
            "code": "DATABASE_ERROR"
        }
    )

def handle_external_service_error(service: str, error: Exception) -> HTTPException:
    """
    Manejar error de servicio externo
    
    Args:
        service: Nombre del servicio
        error: Error del servicio
    
    Returns:
        HTTPException: Excepción HTTP
    """
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "error": "External Service Error",
            "message": f"An error occurred while accessing {service}",
            "code": "EXTERNAL_SERVICE_ERROR"
        }
    )

def handle_websocket_error(error: Exception) -> Dict[str, Any]:
    """
    Manejar error de WebSocket
    
    Args:
        error: Error de WebSocket
    
    Returns:
        Dict[str, Any]: Mensaje de error
    """
    return {
        "type": "error",
        "data": {
            "error": "WebSocket Error",
            "message": str(error),
            "code": "WEBSOCKET_ERROR"
        }
    } 