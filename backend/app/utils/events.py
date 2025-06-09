import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Union
from datetime import datetime
from functools import wraps
from app.utils.logging import get_logger, log_background_task

logger = get_logger(__name__)

class EventManager:
    """Gestor de eventos"""
    
    def __init__(self):
        """Inicializar gestor de eventos"""
        self._handlers: Dict[str, Set[Callable]] = {}
        self._async_handlers: Dict[str, Set[Callable]] = {}
    
    def subscribe(
        self,
        event: str,
        handler: Callable,
        is_async: bool = False
    ) -> None:
        """
        Suscribir manejador a evento
        
        Args:
            event: Nombre del evento
            handler: Función manejadora
            is_async: Si es manejador asíncrono
        """
        if is_async:
            if event not in self._async_handlers:
                self._async_handlers[event] = set()
            self._async_handlers[event].add(handler)
        else:
            if event not in self._handlers:
                self._handlers[event] = set()
            self._handlers[event].add(handler)
    
    def unsubscribe(
        self,
        event: str,
        handler: Callable,
        is_async: bool = False
    ) -> bool:
        """
        Desuscribir manejador de evento
        
        Args:
            event: Nombre del evento
            handler: Función manejadora
            is_async: Si es manejador asíncrono
        
        Returns:
            bool: True si se desuscribió correctamente
        """
        if is_async:
            handlers = self._async_handlers.get(event, set())
        else:
            handlers = self._handlers.get(event, set())
        
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False
    
    async def emit(
        self,
        event: str,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Emitir evento
        
        Args:
            event: Nombre del evento
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        """
        # Ejecutar manejadores síncronos
        for handler in self._handlers.get(event, set()):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in sync handler for event {event}: {str(e)}")
        
        # Ejecutar manejadores asíncronos
        for handler in self._async_handlers.get(event, set()):
            try:
                await handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in async handler for event {event}: {str(e)}")
    
    def clear(self, event: Optional[str] = None) -> None:
        """
        Limpiar manejadores
        
        Args:
            event: Nombre del evento (opcional)
        """
        if event:
            self._handlers.pop(event, None)
            self._async_handlers.pop(event, None)
        else:
            self._handlers.clear()
            self._async_handlers.clear()

def event_handler(event: str, is_async: bool = False):
    """
    Decorador para manejadores de eventos
    
    Args:
        event: Nombre del evento
        is_async: Si es manejador asíncrono
    
    Returns:
        Callable: Función decorada
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = datetime.now()
            try:
                if is_async:
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                status = "completed"
                return result
            except Exception as e:
                logger.error(f"Error in event handler {func.__name__}: {str(e)}")
                status = "failed"
                raise
            finally:
                duration = (datetime.now() - start_time).total_seconds()
                log_background_task(
                    logger,
                    f"event_handler_{func.__name__}",
                    status,
                    duration
                )
        
        # Registrar manejador
        event_manager.subscribe(event, wrapper, is_async)
        return wrapper
    
    return decorator

# Instancia global del gestor de eventos
event_manager = EventManager()

# Eventos predefinidos
class Events:
    """Eventos predefinidos"""
    
    # Eventos de usuario
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    
    # Eventos de viaje
    TRAVEL_CREATED = "travel.created"
    TRAVEL_UPDATED = "travel.updated"
    TRAVEL_DELETED = "travel.deleted"
    TRAVEL_INVITED = "travel.invited"
    TRAVEL_JOINED = "travel.joined"
    TRAVEL_LEFT = "travel.left"
    
    # Eventos de chat
    CHAT_MESSAGE_SENT = "chat.message.sent"
    CHAT_MESSAGE_DELETED = "chat.message.deleted"
    CHAT_ROOM_CREATED = "chat.room.created"
    CHAT_ROOM_DELETED = "chat.room.deleted"
    
    # Eventos de notificación
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_DELETED = "notification.deleted"
    
    # Eventos de archivo
    FILE_UPLOADED = "file.uploaded"
    FILE_DELETED = "file.deleted"
    
    # Eventos de sistema
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error" 