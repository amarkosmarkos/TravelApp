from typing import Optional, Tuple, List, Union
import os
import uuid
import aiofiles
import magic
from datetime import datetime
from fastapi import UploadFile
from app.config import settings
import shutil
from pathlib import Path
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Tipos MIME permitidos
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime"
}

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/webm"
}

# Tamaños máximos (en bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB

def get_file_type(file_path: Union[str, Path]) -> str:
    """
    Obtener tipo MIME de un archivo
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        str: Tipo MIME
    """
    return magic.from_file(str(file_path), mime=True)

def validate_file_type(
    file_path: Union[str, Path],
    allowed_types: set
) -> bool:
    """
    Validar tipo de archivo
    
    Args:
        file_path: Ruta del archivo
        allowed_types: Tipos MIME permitidos
    
    Returns:
        bool: True si el tipo es válido
    """
    file_type = get_file_type(file_path)
    return file_type in allowed_types

def validate_file_size(
    file_path: Union[str, Path],
    max_size: int
) -> bool:
    """
    Validar tamaño de archivo
    
    Args:
        file_path: Ruta del archivo
        max_size: Tamaño máximo en bytes
    
    Returns:
        bool: True si el tamaño es válido
    """
    return os.path.getsize(file_path) <= max_size

async def save_upload_file(
    upload_file: UploadFile,
    destination: Union[str, Path],
    allowed_types: Optional[set] = None,
    max_size: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Guardar archivo subido
    
    Args:
        upload_file: Archivo subido
        destination: Ruta de destino
        allowed_types: Tipos MIME permitidos
        max_size: Tamaño máximo en bytes
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Guardar archivo temporalmente
        temp_path = f"/tmp/{uuid.uuid4()}"
        async with aiofiles.open(temp_path, "wb") as f:
            content = await upload_file.read()
            await f.write(content)
        
        # Validar tipo
        if allowed_types and not validate_file_type(temp_path, allowed_types):
            os.remove(temp_path)
            return False, "Tipo de archivo no permitido"
        
        # Validar tamaño
        if max_size and not validate_file_size(temp_path, max_size):
            os.remove(temp_path)
            return False, "Archivo demasiado grande"
        
        # Mover a destino final
        shutil.move(temp_path, destination)
        return True, "Archivo guardado correctamente"
    
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return False, str(e)

async def save_image(
    upload_file: UploadFile,
    destination: Union[str, Path]
) -> Tuple[bool, str]:
    """
    Guardar imagen
    
    Args:
        upload_file: Archivo subido
        destination: Ruta de destino
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    return await save_upload_file(
        upload_file=upload_file,
        destination=destination,
        allowed_types=ALLOWED_IMAGE_TYPES,
        max_size=MAX_IMAGE_SIZE
    )

async def save_document(
    upload_file: UploadFile,
    destination: Union[str, Path]
) -> Tuple[bool, str]:
    """
    Guardar documento
    
    Args:
        upload_file: Archivo subido
        destination: Ruta de destino
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    return await save_upload_file(
        upload_file=upload_file,
        destination=destination,
        allowed_types=ALLOWED_DOCUMENT_TYPES,
        max_size=MAX_DOCUMENT_SIZE
    )

async def save_video(
    upload_file: UploadFile,
    destination: Union[str, Path]
) -> Tuple[bool, str]:
    """
    Guardar video
    
    Args:
        upload_file: Archivo subido
        destination: Ruta de destino
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    return await save_upload_file(
        upload_file=upload_file,
        destination=destination,
        allowed_types=ALLOWED_VIDEO_TYPES,
        max_size=MAX_VIDEO_SIZE
    )

async def save_audio(
    upload_file: UploadFile,
    destination: Union[str, Path]
) -> Tuple[bool, str]:
    """
    Guardar audio
    
    Args:
        upload_file: Archivo subido
        destination: Ruta de destino
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    return await save_upload_file(
        upload_file=upload_file,
        destination=destination,
        allowed_types=ALLOWED_AUDIO_TYPES,
        max_size=MAX_AUDIO_SIZE
    )

def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Eliminar archivo
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False

def get_file_info(file_path: Union[str, Path]) -> dict:
    """
    Obtener información de archivo
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        dict: Información del archivo
    """
    try:
        stat = os.stat(file_path)
        return {
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "type": get_file_type(file_path),
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        }
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return {}

def list_directory(
    directory: Union[str, Path],
    recursive: bool = False
) -> List[dict]:
    """
    Listar archivos en directorio
    
    Args:
        directory: Ruta del directorio
        recursive: Si es True, lista recursivamente
    
    Returns:
        List[dict]: Lista de archivos
    """
    try:
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(get_file_info(file_path))
            if not recursive:
                break
        return files
    except Exception as e:
        logger.error(f"Error listing directory: {str(e)}")
        return []

def create_directory(
    directory: Union[str, Path],
    recursive: bool = True
) -> bool:
    """
    Crear directorio
    
    Args:
        directory: Ruta del directorio
        recursive: Si es True, crea directorios padres
    
    Returns:
        bool: True si se creó correctamente
    """
    try:
        os.makedirs(directory, exist_ok=recursive)
        return True
    except Exception as e:
        logger.error(f"Error creating directory: {str(e)}")
        return False

def delete_directory(
    directory: Union[str, Path],
    recursive: bool = True
) -> bool:
    """
    Eliminar directorio
    
    Args:
        directory: Ruta del directorio
        recursive: Si es True, elimina recursivamente
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        if recursive:
            shutil.rmtree(directory)
        else:
            os.rmdir(directory)
        return True
    except Exception as e:
        logger.error(f"Error deleting directory: {str(e)}")
        return False

def get_file_extension(filename: str) -> str:
    """
    Obtener extensión de archivo
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        str: Extensión del archivo
    """
    return os.path.splitext(filename)[1].lower()

def is_valid_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validar tipo de archivo
    
    Args:
        filename: Nombre del archivo
        allowed_extensions: Extensiones permitidas
    
    Returns:
        bool: True si el tipo es válido
    """
    return get_file_extension(filename) in allowed_extensions

def get_file_size(file_path: str) -> int:
    """
    Obtener tamaño de archivo
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        int: Tamaño en bytes
    """
    return os.path.getsize(file_path)

def format_file_size(size_in_bytes: int) -> str:
    """
    Formatear tamaño de archivo
    
    Args:
        size_in_bytes: Tamaño en bytes
    
    Returns:
        str: Tamaño formateado
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB" 