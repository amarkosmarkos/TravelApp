import logging
import sys
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime
from app.config import settings

class JSONFormatter(logging.Formatter):
    """Formateador de logs en JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatear registro de log a JSON
        
        Args:
            record: Registro de log
        
        Returns:
            str: Registro formateado en JSON
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar excepción si existe
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Agregar datos extra si existen
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def setup_logging(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configurar sistema de logging
    
    Args:
        log_file: Ruta del archivo de log
        log_level: Nivel de logging
        max_bytes: Tamaño máximo del archivo
        backup_count: Número de archivos de respaldo
    """
    # Crear directorio de logs si no existe
    if log_file:
        log_path = Path(log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
    
    # Configurar formato
    json_formatter = JSONFormatter()
    
    # Configurar handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    
    # Configurar handler de archivo si se especifica
    handlers = [console_handler]
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(json_formatter)
        handlers.append(file_handler)
    
    # Configurar logger raíz
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger con nombre
    
    Args:
        name: Nombre del logger
    
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)

def log_error(
    logger: logging.Logger,
    message: str,
    error: Exception,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar error con detalles
    
    Args:
        logger: Logger a usar
        message: Mensaje de error
        error: Excepción
        extra: Datos adicionales
    """
    extra = extra or {}
    extra.update({
        "error_type": error.__class__.__name__,
        "error_message": str(error)
    })
    logger.error(message, exc_info=True, extra=extra)

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar petición HTTP
    
    Args:
        logger: Logger a usar
        method: Método HTTP
        path: Ruta
        status_code: Código de estado
        duration: Duración en segundos
        extra: Datos adicionales
    """
    extra = extra or {}
    extra.update({
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration": duration
    })
    logger.info("HTTP Request", extra=extra)

def log_database(
    logger: logging.Logger,
    operation: str,
    collection: str,
    duration: float,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar operación de base de datos
    
    Args:
        logger: Logger a usar
        operation: Operación realizada
        collection: Colección afectada
        duration: Duración en segundos
        extra: Datos adicionales
    """
    extra = extra or {}
    extra.update({
        "operation": operation,
        "collection": collection,
        "duration": duration
    })
    logger.info("Database Operation", extra=extra)

def log_cache(
    logger: logging.Logger,
    operation: str,
    key: str,
    duration: float,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar operación de caché
    
    Args:
        logger: Logger a usar
        operation: Operación realizada
        key: Clave afectada
        duration: Duración en segundos
        extra: Datos adicionales
    """
    extra = extra or {}
    extra.update({
        "operation": operation,
        "key": key,
        "duration": duration
    })
    logger.info("Cache Operation", extra=extra)

def log_email(
    logger: logging.Logger,
    recipient: str,
    subject: str,
    template: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar envío de email
    
    Args:
        logger: Logger a usar
        recipient: Destinatario
        subject: Asunto
        template: Plantilla usada
        extra: Datos adicionales
    """
    extra = extra or {}
    extra.update({
        "recipient": recipient,
        "subject": subject,
        "template": template
    })
    logger.info("Email Sent", extra=extra)

def log_websocket(
    logger: logging.Logger,
    event: str,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar evento de WebSocket
    
    Args:
        logger: Logger a usar
        event: Evento ocurrido
        user_id: ID de usuario
        extra: Datos adicionales
    """
    extra = extra or {}
    if user_id:
        extra["user_id"] = user_id
    extra["event"] = event
    logger.info("WebSocket Event", extra=extra)

def log_background_task(
    logger: logging.Logger,
    task_name: str,
    status: str,
    duration: float,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Registrar tarea en segundo plano
    
    Args:
        logger: Logger a usar
        task_name: Nombre de la tarea
        status: Estado de la tarea
        duration: Duración en segundos
        extra: Datos adicionales
    """
    extra = extra or {}
    extra.update({
        "task_name": task_name,
        "status": status,
        "duration": duration
    })
    logger.info("Background Task", extra=extra)

class RequestLogger:
    """Logger para requests HTTP"""
    
    def __init__(self):
        self.logger = logging.getLogger("request")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        client_ip: str,
        user_id: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Loggear request
        
        Args:
            method: Método HTTP
            path: Ruta
            status_code: Código de estado
            duration: Duración en segundos
            client_ip: IP del cliente
            user_id: ID del usuario
            error: Error si ocurrió
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": f"{duration:.3f}s",
            "client_ip": client_ip
        }
        
        if user_id:
            log_data["user_id"] = user_id
        
        if error:
            log_data["error"] = str(error)
            self.logger.error(f"Request failed: {log_data}")
        else:
            self.logger.info(f"Request completed: {log_data}")

class SecurityLogger:
    """Logger para eventos de seguridad"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    def log_auth_attempt(
        self,
        user_id: Optional[str],
        success: bool,
        method: str,
        error: Optional[Exception] = None
    ) -> None:
        """
        Loggear intento de autenticación
        
        Args:
            user_id: ID del usuario
            success: Si fue exitoso
            method: Método de autenticación
            error: Error si ocurrió
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "success": success,
            "method": method
        }
        
        if error:
            log_data["error"] = str(error)
            self.logger.warning(f"Authentication failed: {log_data}")
        else:
            self.logger.info(f"Authentication successful: {log_data}")
    
    def log_rate_limit(
        self,
        client_ip: str,
        path: str,
        limit: int,
        window: int
    ) -> None:
        """
        Loggear límite de tasa
        
        Args:
            client_ip: IP del cliente
            path: Ruta
            limit: Límite de requests
            window: Ventana de tiempo en segundos
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "path": path,
            "limit": limit,
            "window": f"{window}s"
        }
        
        self.logger.warning(f"Rate limit exceeded: {log_data}")

class DatabaseLogger:
    """Logger para operaciones de base de datos"""
    
    def __init__(self):
        self.logger = logging.getLogger("database")
    
    def log_query(
        self,
        operation: str,
        collection: str,
        duration: float,
        error: Optional[Exception] = None
    ) -> None:
        """
        Loggear query
        
        Args:
            operation: Operación (find, insert, update, delete)
            collection: Colección
            duration: Duración en segundos
            error: Error si ocurrió
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "collection": collection,
            "duration": f"{duration:.3f}s"
        }
        
        if error:
            log_data["error"] = str(error)
            self.logger.error(f"Database operation failed: {log_data}")
        else:
            self.logger.debug(f"Database operation completed: {log_data}")

# Instancias de loggers
request_logger = RequestLogger()
security_logger = SecurityLogger()
database_logger = DatabaseLogger()

# Configurar logger por defecto
logger = get_logger(__name__) 