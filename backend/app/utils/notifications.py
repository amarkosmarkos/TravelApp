import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from fastapi import WebSocket
from app.database import get_database
from app.utils.email import send_notification_email
from app.utils.websocket import manager as ws_manager
from app.config import settings
from app.utils.logging import get_logger
from app.utils.events import event_manager, Events

logger = get_logger(__name__)

# Conexiones WebSocket activas
active_connections: Dict[str, List[WebSocket]] = {}

class NotificationType:
    """Tipos de notificación"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    
    # Notificaciones de usuario
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOGGED_IN = "user_logged_in"
    USER_LOGGED_OUT = "user_logged_out"
    
    # Notificaciones de viaje
    TRAVEL_CREATED = "travel_created"
    TRAVEL_UPDATED = "travel_updated"
    TRAVEL_DELETED = "travel_deleted"
    TRAVEL_INVITATION = "travel_invitation"
    TRAVEL_INVITATION_ACCEPTED = "travel_invitation_accepted"
    TRAVEL_INVITATION_DECLINED = "travel_invitation_declined"
    
    # Notificaciones de chat
    CHAT_MESSAGE = "chat_message"
    CHAT_MENTION = "chat_mention"
    CHAT_REACTION = "chat_reaction"
    
    # Notificaciones de archivo
    FILE_UPLOADED = "file_uploaded"
    FILE_DELETED = "file_deleted"
    FILE_SHARED = "file_shared"

class Notification:
    """Clase para representar una notificación"""
    
    def __init__(
        self,
        type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.type = type
        self.title = title
        self.message = message
        self.data = data or {}
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convertir a JSON"""
        return json.dumps(self.to_dict())

async def connect_websocket(
    websocket: WebSocket,
    user_id: str
) -> None:
    """
    Conectar WebSocket
    
    Args:
        websocket: Conexión WebSocket
        user_id: ID del usuario
    """
    await websocket.accept()
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)

async def disconnect_websocket(
    websocket: WebSocket,
    user_id: str
) -> None:
    """
    Desconectar WebSocket
    
    Args:
        websocket: Conexión WebSocket
        user_id: ID del usuario
    """
    if user_id in active_connections:
        active_connections[user_id].remove(websocket)
        if not active_connections[user_id]:
            del active_connections[user_id]

async def send_notification(
    notification: Notification,
    send_email: bool = True
) -> None:
    """
    Enviar notificación
    
    Args:
        notification: Notificación a enviar
        send_email: Si es True, envía email
    """
    try:
        # Enviar por WebSocket
        if notification.user_id in active_connections:
            for websocket in active_connections[notification.user_id]:
                await websocket.send_text(notification.to_json())
        
        # Enviar por email
        if send_email and notification.user_id:
            await send_notification_email(
                email_to=notification.data.get("email"),
                notification_type=notification.type,
                notification_data=notification.data,
                action_url=notification.data.get("action_url")
            )
        
        # Emitir evento
        await event_manager.emit(
            Events.NOTIFICATION_CREATED,
            notification.to_dict()
        )
        
        logger.info(f"Notification sent: {notification.type}")
    
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")

async def send_user_notification(
    user_id: str,
    type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    send_email: bool = True
) -> None:
    """
    Enviar notificación a usuario
    
    Args:
        user_id: ID del usuario
        type: Tipo de notificación
        title: Título
        message: Mensaje
        data: Datos adicionales
        send_email: Si es True, envía email
    """
    notification = Notification(
        type=type,
        title=title,
        message=message,
        data=data,
        user_id=user_id
    )
    await send_notification(notification, send_email)

async def send_travel_notification(
    travel_id: str,
    type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    user_ids: Optional[List[str]] = None,
    send_email: bool = True
) -> None:
    """
    Enviar notificación de viaje
    
    Args:
        travel_id: ID del viaje
        type: Tipo de notificación
        title: Título
        message: Mensaje
        data: Datos adicionales
        user_ids: IDs de usuarios
        send_email: Si es True, envía email
    """
    if not user_ids:
        return
    
    notification_data = {
        "travel_id": travel_id
    }
    if data:
        notification_data.update(data)
    
    for user_id in user_ids:
        notification = Notification(
            type=type,
            title=title,
            message=message,
            data=notification_data,
            user_id=user_id
        )
        await send_notification(notification, send_email)

async def send_chat_notification(
    chat_id: str,
    type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    user_ids: Optional[List[str]] = None,
    send_email: bool = True
) -> None:
    """
    Enviar notificación de chat
    
    Args:
        chat_id: ID del chat
        type: Tipo de notificación
        title: Título
        message: Mensaje
        data: Datos adicionales
        user_ids: IDs de usuarios
        send_email: Si es True, envía email
    """
    if not user_ids:
        return
    
    notification_data = {
        "chat_id": chat_id
    }
    if data:
        notification_data.update(data)
    
    for user_id in user_ids:
        notification = Notification(
            type=type,
            title=title,
            message=message,
            data=notification_data,
            user_id=user_id
        )
        await send_notification(notification, send_email)

async def send_file_notification(
    file_id: str,
    type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    user_ids: Optional[List[str]] = None,
    send_email: bool = True
) -> None:
    """
    Enviar notificación de archivo
    
    Args:
        file_id: ID del archivo
        type: Tipo de notificación
        title: Título
        message: Mensaje
        data: Datos adicionales
        user_ids: IDs de usuarios
        send_email: Si es True, envía email
    """
    if not user_ids:
        return
    
    notification_data = {
        "file_id": file_id
    }
    if data:
        notification_data.update(data)
    
    for user_id in user_ids:
        notification = Notification(
            type=type,
            title=title,
            message=message,
            data=notification_data,
            user_id=user_id
        )
        await send_notification(notification, send_email)

async def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    priority: str = NotificationPriority.MEDIUM,
    email_notification: bool = True,
    push_notification: bool = True
) -> Dict[str, Any]:
    """
    Crear notificación
    
    Args:
        user_id: ID del usuario
        notification_type: Tipo de notificación
        title: Título de la notificación
        message: Mensaje de la notificación
        data: Datos adicionales
        priority: Prioridad de la notificación
        email_notification: Si se debe enviar por email
        push_notification: Si se debe enviar por push
    
    Returns:
        Dict[str, Any]: Notificación creada
    """
    try:
        # Crear notificación en base de datos
        notification = {
            "user_id": user_id,
            "type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "priority": priority,
            "read": False,
            "created_at": datetime.utcnow()
        }
        
        # Guardar en base de datos
        db = await get_database()
        result = await db.notifications.insert_one(notification)
        notification["_id"] = str(result.inserted_id)
        
        # Enviar por WebSocket
        if push_notification:
            await ws_manager.send_personal_message(
                user_id=user_id,
                message={
                    "type": "notification",
                    "data": notification
                }
            )
        
        # Enviar por email
        if email_notification:
            await send_notification_email(
                email_to=notification["data"].get("user_email"),
                notification_type=notification_type,
                notification_data=notification
            )
        
        logger.info(f"Notification created for user {user_id}: {notification_type}")
        return notification
    
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise

async def get_user_notifications(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Obtener notificaciones de usuario
    
    Args:
        user_id: ID del usuario
        skip: Número de notificaciones a saltar
        limit: Límite de notificaciones
        unread_only: Si solo se deben obtener no leídas
    
    Returns:
        List[Dict[str, Any]]: Lista de notificaciones
    """
    try:
        db = await get_database()
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False
        
        cursor = db.notifications.find(query)
        cursor.sort("created_at", -1)
        cursor.skip(skip).limit(limit)
        
        notifications = await cursor.to_list(length=limit)
        return [format_document(n) for n in notifications]
    
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise

async def mark_notification_as_read(notification_id: str) -> bool:
    """
    Marcar notificación como leída
    
    Args:
        notification_id: ID de la notificación
    
    Returns:
        bool: True si se marcó como leída
    """
    try:
        db = await get_database()
        result = await db.notifications.update_one(
            {"_id": parse_object_id(notification_id)},
            {"$set": {"read": True, "read_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise

async def mark_all_notifications_as_read(user_id: str) -> bool:
    """
    Marcar todas las notificaciones como leídas
    
    Args:
        user_id: ID del usuario
    
    Returns:
        bool: True si se marcaron como leídas
    """
    try:
        db = await get_database()
        result = await db.notifications.update_many(
            {"user_id": user_id, "read": False},
            {"$set": {"read": True, "read_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise

async def delete_notification(notification_id: str) -> bool:
    """
    Eliminar notificación
    
    Args:
        notification_id: ID de la notificación
    
    Returns:
        bool: True si se eliminó
    """
    try:
        db = await get_database()
        result = await db.notifications.delete_one(
            {"_id": parse_object_id(notification_id)}
        )
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise

async def delete_all_notifications(user_id: str) -> bool:
    """
    Eliminar todas las notificaciones
    
    Args:
        user_id: ID del usuario
    
    Returns:
        bool: True si se eliminaron
    """
    try:
        db = await get_database()
        result = await db.notifications.delete_many({"user_id": user_id})
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Error deleting all notifications: {str(e)}")
        raise

async def get_unread_notifications_count(user_id: str) -> int:
    """
    Obtener cantidad de notificaciones no leídas
    
    Args:
        user_id: ID del usuario
    
    Returns:
        int: Cantidad de notificaciones no leídas
    """
    try:
        db = await get_database()
        count = await db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })
        return count
    
    except Exception as e:
        logger.error(f"Error getting unread notifications count: {str(e)}")
        raise 