from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    """Modelo base para respuestas"""
    success: bool
    message: str
    data: Optional[T] = None

class PaginationModel(BaseModel):
    """Modelo para paginación"""
    page: int
    page_size: int
    total_pages: int
    total_items: int

class PaginatedResponse(ResponseModel, Generic[T]):
    """Modelo para respuestas paginadas"""
    pagination: PaginationModel
    data: List[T]

class ErrorResponse(ResponseModel):
    """Modelo para respuestas de error"""
    error_code: str
    error_details: Optional[Any] = None

class TokenResponse(ResponseModel):
    """Modelo para respuesta de token"""
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(ResponseModel):
    """Modelo para respuesta de usuario"""
    id: str
    email: str
    full_name: str
    is_active: bool
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

class TravelResponse(ResponseModel):
    """Modelo para respuesta de viaje"""
    id: str
    title: str
    description: str
    destination: str
    start_date: datetime
    end_date: datetime
    status: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(ResponseModel):
    """Modelo para respuesta de mensaje"""
    id: str
    content: str
    type: str
    travel_id: str
    user_id: str
    created_at: datetime

class SearchResponse(ResponseModel):
    """Modelo para respuesta de búsqueda"""
    query: str
    filters: Optional[dict]
    sort: Optional[dict]
    results: List[Any]

class HealthCheckResponse(ResponseModel):
    """Modelo para respuesta de estado de salud"""
    status: str
    version: str
    timestamp: datetime
    services: dict 