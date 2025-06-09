from typing import Dict, List

# Roles y permisos
ROLES: Dict[str, List[str]] = {
    "admin": [
        "manage_users",
        "manage_roles",
        "manage_travels",
        "view_reports"
    ],
    "manager": [
        "manage_travels",
        "view_reports"
    ],
    "user": [
        "create_travel",
        "view_own_travels",
        "edit_own_travels"
    ]
}

# Estados de viaje
TRAVEL_STATUS = {
    "PLANNING": "planning",
    "CONFIRMED": "confirmed",
    "IN_PROGRESS": "in_progress",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled"
}

# Tipos de mensajes
MESSAGE_TYPES = {
    "TEXT": "text",
    "IMAGE": "image",
    "LOCATION": "location",
    "DOCUMENT": "document"
}

# Configuración de paginación
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Configuración de búsqueda
SEARCH_FIELDS = {
    "travel": ["title", "description", "destination"],
    "user": ["email", "full_name"]
}

# Configuración de ordenamiento
SORT_FIELDS = {
    "travel": ["created_at", "updated_at", "start_date", "end_date"],
    "user": ["created_at", "last_login", "full_name"]
}

# Configuración de filtros
FILTER_OPERATORS = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "in": "in",
    "nin": "not in",
    "regex": "regex"
}

# Configuración de caché
CACHE_TTL = {
    "user": 300,  # 5 minutos
    "travel": 600,  # 10 minutos
    "search": 300  # 5 minutos
}

# Configuración de validación
VALIDATION = {
    "password": {
        "min_length": 8,
        "max_length": 100,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True
    },
    "email": {
        "max_length": 255
    },
    "name": {
        "min_length": 2,
        "max_length": 100
    }
}

# Configuración de archivos
FILE_UPLOAD = {
    "max_size": 5 * 1024 * 1024,  # 5MB
    "allowed_types": [
        "image/jpeg",
        "image/png",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
} 