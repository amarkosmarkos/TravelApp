from datetime import datetime
from typing import Any, Dict, Optional
from bson import ObjectId
import json

def format_datetime(dt: datetime) -> str:
    """Formatear datetime a string ISO"""
    return dt.isoformat()

def parse_datetime(dt_str: str) -> datetime:
    """Parsear string ISO a datetime"""
    return datetime.fromisoformat(dt_str)

def format_object_id(obj_id: ObjectId) -> str:
    """Formatear ObjectId a string"""
    return str(obj_id)

def parse_object_id(obj_id_str: str) -> ObjectId:
    """Parsear string a ObjectId"""
    return ObjectId(obj_id_str)

def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Limpiar diccionario de valores None"""
    return {k: v for k, v in data.items() if v is not None}

def json_serial(obj: Any) -> str:
    """Serializar objetos a JSON"""
    if isinstance(obj, datetime):
        return format_datetime(obj)
    if isinstance(obj, ObjectId):
        return format_object_id(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_json_loads(json_str: str) -> Optional[Dict[str, Any]]:
    """Cargar JSON de forma segura"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def safe_json_dumps(data: Dict[str, Any]) -> Optional[str]:
    """Guardar JSON de forma segura"""
    try:
        return json.dumps(data, default=json_serial)
    except TypeError:
        return None 