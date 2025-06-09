from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime
from app.exceptions import ValidationError
from pydantic import BaseModel, ValidationError
import logging
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Patrones de validación
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PASSWORD_PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$"
PHONE_PATTERN = r"^\+?[1-9]\d{1,14}$"
URL_PATTERN = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
CURRENCY_PATTERN = r"^[A-Z]{3}$"
LANGUAGE_PATTERN = r"^[a-z]{2}(-[A-Z]{2})?$"
TIMEZONE_PATTERN = r"^[A-Za-z]+\/[A-Za-z_]+$"

def validate_email(email: str) -> bool:
    """
    Validar formato de email
    
    Args:
        email: Email a validar
    
    Returns:
        bool: True si es válido
    """
    return bool(re.match(EMAIL_PATTERN, email))

def validate_password(password: str) -> bool:
    """
    Validar formato de contraseña
    
    Args:
        password: Contraseña a validar
    
    Returns:
        bool: True si es válida
    """
    return bool(re.match(PASSWORD_PATTERN, password))

def validate_phone(phone: str) -> bool:
    """
    Validar formato de teléfono
    
    Args:
        phone: Teléfono a validar
    
    Returns:
        bool: True si es válido
    """
    return bool(re.match(PHONE_PATTERN, phone))

def validate_url(url: str) -> bool:
    """
    Validar formato de URL
    
    Args:
        url: URL a validar
    
    Returns:
        bool: True si es válida
    """
    return bool(re.match(URL_PATTERN, url))

def validate_currency(currency: str) -> bool:
    """
    Validar código de moneda
    
    Args:
        currency: Código de moneda a validar
    
    Returns:
        bool: True si es válido
    """
    return bool(re.match(CURRENCY_PATTERN, currency))

def validate_language(language: str) -> bool:
    """
    Validar código de idioma
    
    Args:
        language: Código de idioma a validar
    
    Returns:
        bool: True si es válido
    """
    return bool(re.match(LANGUAGE_PATTERN, language))

def validate_timezone(timezone: str) -> bool:
    """
    Validar zona horaria
    
    Args:
        timezone: Zona horaria a validar
    
    Returns:
        bool: True si es válida
    """
    return bool(re.match(TIMEZONE_PATTERN, timezone))

def validate_date(date_str: str) -> bool:
    """
    Validar formato de fecha
    
    Args:
        date_str: Fecha a validar en formato ISO
    
    Returns:
        bool: True si es válida
    """
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False

def validate_model(data: Dict[str, Any], model: BaseModel) -> bool:
    """
    Validar datos contra modelo Pydantic
    
    Args:
        data: Datos a validar
        model: Modelo Pydantic
    
    Returns:
        bool: True si es válido
    """
    try:
        model(**data)
        return True
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def sanitize_input(text: str) -> str:
    """
    Sanitizar entrada de texto
    
    Args:
        text: Texto a sanitizar
    
    Returns:
        str: Texto sanitizado
    """
    # Eliminar caracteres especiales
    text = re.sub(r"[^\w\s-]", "", text)
    # Eliminar espacios extra
    text = re.sub(r"\s+", " ", text)
    # Eliminar espacios al inicio y final
    return text.strip()

def validate_file_type(
    filename: str,
    allowed_types: List[str]
) -> bool:
    """
    Validar tipo de archivo
    
    Args:
        filename: Nombre del archivo
        allowed_types: Lista de tipos permitidos
    
    Returns:
        bool: True si es válido
    """
    extension = filename.split(".")[-1].lower()
    return extension in allowed_types

def validate_file_size(
    size: int,
    max_size: int
) -> bool:
    """
    Validar tamaño de archivo
    
    Args:
        size: Tamaño en bytes
        max_size: Tamaño máximo en bytes
    
    Returns:
        bool: True si es válido
    """
    return size <= max_size

def validate_coordinates(
    latitude: float,
    longitude: float
) -> bool:
    """
    Validar coordenadas geográficas
    
    Args:
        latitude: Latitud
        longitude: Longitud
    
    Returns:
        bool: True si son válidas
    """
    return (
        -90 <= latitude <= 90 and
        -180 <= longitude <= 180
    )

def validate_pagination(
    page: int,
    page_size: int,
    max_page_size: int = 100
) -> bool:
    """
    Validar parámetros de paginación
    
    Args:
        page: Número de página
        page_size: Tamaño de página
        max_page_size: Tamaño máximo de página
    
    Returns:
        bool: True si son válidos
    """
    return (
        page > 0 and
        0 < page_size <= max_page_size
    )

def validate_search_query(
    query: str,
    min_length: int = 3,
    max_length: int = 100
) -> bool:
    """
    Validar consulta de búsqueda
    
    Args:
        query: Consulta a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
    
    Returns:
        bool: True si es válida
    """
    return (
        len(query) >= min_length and
        len(query) <= max_length
    )

def validate_sort_params(
    sort_by: str,
    sort_order: str,
    allowed_fields: List[str]
) -> bool:
    """
    Validar parámetros de ordenamiento
    
    Args:
        sort_by: Campo para ordenar
        sort_order: Orden (asc/desc)
        allowed_fields: Campos permitidos
    
    Returns:
        bool: True si son válidos
    """
    return (
        sort_by in allowed_fields and
        sort_order in ["asc", "desc"]
    )

def validate_filter_params(
    filters: Dict[str, Any],
    allowed_fields: List[str]
) -> bool:
    """
    Validar parámetros de filtrado
    
    Args:
        filters: Filtros a validar
        allowed_fields: Campos permitidos
    
    Returns:
        bool: True si son válidos
    """
    return all(
        field in allowed_fields
        for field in filters.keys()
    )

def validate_date_range(
    start_date: str,
    end_date: str
) -> bool:
    """
    Validar rango de fechas
    
    Args:
        start_date: Fecha inicial
        end_date: Fecha final
    
    Returns:
        bool: True si es válido
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return start <= end
    except ValueError:
        return False

def validate_numeric_range(
    min_value: Union[int, float],
    max_value: Union[int, float]
) -> bool:
    """
    Validar rango numérico
    
    Args:
        min_value: Valor mínimo
        max_value: Valor máximo
    
    Returns:
        bool: True si es válido
    """
    return min_value <= max_value

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validar campos requeridos
    
    Args:
        data: Datos a validar
        required_fields: Lista de campos requeridos
    
    Raises:
        ValidationError: Si falta algún campo requerido
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_field_type(value: Any, expected_type: type) -> bool:
    """
    Validar tipo de campo
    
    Args:
        value: Valor a validar
        expected_type: Tipo esperado
    
    Returns:
        bool: True si el tipo es válido
    """
    return isinstance(value, expected_type)

def validate_field_length(value: Union[str, List], min_length: Optional[int] = None, max_length: Optional[int] = None) -> bool:
    """
    Validar longitud de campo
    
    Args:
        value: Valor a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
    
    Returns:
        bool: True si la longitud es válida
    """
    length = len(value)
    if min_length is not None and length < min_length:
        return False
    if max_length is not None and length > max_length:
        return False
    return True

def validate_enum(value: Any, allowed_values: List[Any]) -> bool:
    """
    Validar valor de enumeración
    
    Args:
        value: Valor a validar
        allowed_values: Lista de valores permitidos
    
    Returns:
        bool: True si el valor está permitido
    """
    return value in allowed_values

def validate_regex(value: str, pattern: str) -> bool:
    """
    Validar expresión regular
    
    Args:
        value: Valor a validar
        pattern: Patrón de expresión regular
    
    Returns:
        bool: True si el valor coincide con el patrón
    """
    return bool(re.match(pattern, value))

def validate_unique_fields(data: Dict[str, Any], unique_fields: List[str], existing_data: List[Dict[str, Any]]) -> None:
    """
    Validar campos únicos
    
    Args:
        data: Datos a validar
        unique_fields: Lista de campos únicos
        existing_data: Lista de datos existentes
    
    Raises:
        ValidationError: Si algún campo único ya existe
    """
    for field in unique_fields:
        if field in data:
            value = data[field]
            for item in existing_data:
                if item.get(field) == value:
                    raise ValidationError(f"Field '{field}' with value '{value}' already exists")
