from typing import TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from math import ceil
from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.exceptions import ValidationError

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(default=1, ge=1, description="Número de página")
    page_size: int = Field(default=20, ge=1, le=100, description="Tamaño de página")
    sort_by: Optional[str] = Field(default=None, description="Campo para ordenar")
    sort_order: Optional[str] = Field(default="asc", description="Orden de clasificación (asc/desc)")

class PaginationInfo(BaseModel):
    """Información de paginación"""
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas")
    total_items: int = Field(..., description="Total de items")
    has_next: bool = Field(..., description="Si hay siguiente página")
    has_prev: bool = Field(..., description="Si hay página anterior")

class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada"""
    items: List[T] = Field(..., description="Items de la página")
    pagination: PaginationInfo = Field(..., description="Información de paginación")

def get_pagination_info(
    total_items: int,
    page: int,
    page_size: int
) -> PaginationInfo:
    """
    Obtener información de paginación
    
    Args:
        total_items: Total de items
        page: Página actual
        page_size: Tamaño de página
    
    Returns:
        PaginationInfo: Información de paginación
    """
    total_pages = ceil(total_items / page_size)
    return PaginationInfo(
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_items=total_items,
        has_next=page < total_pages,
        has_prev=page > 1
    )

def get_skip_limit(page: int, page_size: int) -> Dict[str, int]:
    """
    Obtener skip y limit para paginación
    
    Args:
        page: Página actual
        page_size: Tamaño de página
    
    Returns:
        Dict[str, int]: Skip y limit
    """
    skip = (page - 1) * page_size
    return {"skip": skip, "limit": page_size}

def get_sort_params(sort_by: Optional[str], sort_order: Optional[str]) -> Dict[str, int]:
    """
    Obtener parámetros de ordenamiento
    
    Args:
        sort_by: Campo para ordenar
        sort_order: Orden de clasificación
    
    Returns:
        Dict[str, int]: Parámetros de ordenamiento
    """
    if not sort_by:
        return {}
    
    order = 1 if sort_order == "asc" else -1
    return {sort_by: order}

def create_paginated_response(
    items: List[T],
    total_items: int,
    page: int,
    page_size: int
) -> PaginatedResponse[T]:
    """
    Crear respuesta paginada
    
    Args:
        items: Items de la página
        total_items: Total de items
        page: Página actual
        page_size: Tamaño de página
    
    Returns:
        PaginatedResponse[T]: Respuesta paginada
    """
    pagination = get_pagination_info(total_items, page, page_size)
    return PaginatedResponse(items=items, pagination=pagination)

def get_pagination_links(
    base_url: str,
    page: int,
    total_pages: int,
    query_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Optional[str]]:
    """
    Obtener enlaces de paginación
    
    Args:
        base_url: URL base
        page: Página actual
        total_pages: Total de páginas
        query_params: Parámetros de consulta
    
    Returns:
        Dict[str, Optional[str]]: Enlaces de paginación
    """
    query_params = query_params or {}
    links = {
        "first": None,
        "prev": None,
        "next": None,
        "last": None
    }
    
    # Construir URL base con parámetros
    params = query_params.copy()
    base_query = "&".join(f"{k}={v}" for k, v in params.items())
    url_template = f"{base_url}?{base_query}&page={{page}}"
    
    # Primer página
    if page > 1:
        links["first"] = url_template.format(page=1)
    
    # Página anterior
    if page > 1:
        links["prev"] = url_template.format(page=page - 1)
    
    # Siguiente página
    if page < total_pages:
        links["next"] = url_template.format(page=page + 1)
    
    # Última página
    if page < total_pages:
        links["last"] = url_template.format(page=total_pages)
    
    return links

def validate_pagination_params(
    page: int,
    page_size: int,
    max_page_size: int = 100
) -> Dict[str, int]:
    """
    Validar parámetros de paginación
    
    Args:
        page: Página actual
        page_size: Tamaño de página
        max_page_size: Tamaño máximo de página
    
    Returns:
        Dict[str, int]: Parámetros validados
    
    Raises:
        ValueError: Si los parámetros son inválidos
    """
    if page < 1:
        raise ValueError("Page must be greater than 0")
    
    if page_size < 1:
        raise ValueError("Page size must be greater than 0")
    
    if page_size > max_page_size:
        page_size = max_page_size
    
    return {"page": page, "page_size": page_size} 