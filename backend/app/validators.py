import re
from typing import Optional
from app.constants import VALIDATION
from app.exceptions import ValidationError

def validate_password(password: str) -> bool:
    """Validar contraseña"""
    if len(password) < VALIDATION["password"]["min_length"]:
        raise ValidationError(
            f"Password must be at least {VALIDATION['password']['min_length']} characters long"
        )
    
    if len(password) > VALIDATION["password"]["max_length"]:
        raise ValidationError(
            f"Password must be at most {VALIDATION['password']['max_length']} characters long"
        )
    
    if VALIDATION["password"]["require_uppercase"] and not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if VALIDATION["password"]["require_lowercase"] and not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if VALIDATION["password"]["require_digit"] and not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit")
    
    if VALIDATION["password"]["require_special"] and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character")
    
    return True

def validate_email(email: str) -> bool:
    """Validar email"""
    if len(email) > VALIDATION["email"]["max_length"]:
        raise ValidationError(
            f"Email must be at most {VALIDATION['email']['max_length']} characters long"
        )
    
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    return True

def validate_name(name: str) -> bool:
    """Validar nombre"""
    if len(name) < VALIDATION["name"]["min_length"]:
        raise ValidationError(
            f"Name must be at least {VALIDATION['name']['min_length']} characters long"
        )
    
    if len(name) > VALIDATION["name"]["max_length"]:
        raise ValidationError(
            f"Name must be at most {VALIDATION['name']['max_length']} characters long"
        )
    
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValidationError("Name can only contain letters, spaces, hyphens and apostrophes")
    
    return True

def validate_file_size(size: int) -> bool:
    """Validar tamaño de archivo"""
    if size > VALIDATION["file"]["max_size"]:
        raise ValidationError(
            f"File size must be at most {VALIDATION['file']['max_size']} bytes"
        )
    return True

def validate_file_type(content_type: str) -> bool:
    """Validar tipo de archivo"""
    if content_type not in VALIDATION["file"]["allowed_types"]:
        raise ValidationError("File type not allowed")
    return True

def validate_pagination(page: int, page_size: int) -> bool:
    """Validar paginación"""
    if page < 1:
        raise ValidationError("Page number must be greater than 0")
    
    if page_size < 1:
        raise ValidationError("Page size must be greater than 0")
    
    if page_size > VALIDATION["pagination"]["max_page_size"]:
        raise ValidationError(
            f"Page size must be at most {VALIDATION['pagination']['max_page_size']}"
        )
    
    return True

def validate_sort_field(field: str, allowed_fields: list) -> bool:
    """Validar campo de ordenamiento"""
    if field not in allowed_fields:
        raise ValidationError(f"Invalid sort field. Allowed fields: {', '.join(allowed_fields)}")
    return True

def validate_filter_operator(operator: str) -> bool:
    """Validar operador de filtro"""
    if operator not in VALIDATION["filter"]["operators"]:
        raise ValidationError(
            f"Invalid filter operator. Allowed operators: {', '.join(VALIDATION['filter']['operators'])}"
        )
    return True 