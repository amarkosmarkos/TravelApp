from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import logging
from app.utils.common import json_serial, safe_json_dumps
from app.utils.logging import get_logger
from app.utils.events import event_manager, Events

logger = get_logger(__name__)

class ConnectionManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_rooms: Dict[str, Set[str]] = {}
        self.room_users: Dict[str, Set[str]] = {}
    
    async def connect(
        self,
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
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: {user_id}")
    
    async def disconnect(
        self,
        websocket: WebSocket,
        user_id: str
    ) -> None:
        """
        Desconectar WebSocket
        
        Args:
            websocket: Conexión WebSocket
            user_id: ID del usuario
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Eliminar de salas
        if user_id in self.user_rooms:
            for room in self.user_rooms[user_id]:
                if room in self.room_users:
                    self.room_users[room].remove(user_id)
                    if not self.room_users[room]:
                        del self.room_users[room]
            del self.user_rooms[user_id]
        
        logger.info(f"WebSocket disconnected: {user_id}")
    
    async def join_room(
        self,
        user_id: str,
        room: str
    ) -> None:
        """
        Unir usuario a sala
        
        Args:
            user_id: ID del usuario
            room: ID de la sala
        """
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room)
        
        if room not in self.room_users:
            self.room_users[room] = set()
        self.room_users[room].add(user_id)
        
        logger.info(f"User {user_id} joined room {room}")
    
    async def leave_room(
        self,
        user_id: str,
        room: str
    ) -> None:
        """
        Sacar usuario de sala
        
        Args:
            user_id: ID del usuario
            room: ID de la sala
        """
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room)
            if not self.user_rooms[user_id]:
                del self.user_rooms[user_id]
        
        if room in self.room_users:
            self.room_users[room].discard(user_id)
            if not self.room_users[room]:
                del self.room_users[room]
        
        logger.info(f"User {user_id} left room {room}")
    
    async def send_personal_message(
        self,
        message: Dict[str, Any],
        user_id: str
    ) -> None:
        """
        Enviar mensaje personal
        
        Args:
            message: Mensaje a enviar
            user_id: ID del usuario
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {str(e)}")
    
    async def broadcast(
        self,
        message: Dict[str, Any]
    ) -> None:
        """
        Enviar mensaje a todos
        
        Args:
            message: Mensaje a enviar
        """
        for user_id in self.active_connections:
            await self.send_personal_message(message, user_id)
    
    async def broadcast_to_room(
        self,
        message: Dict[str, Any],
        room: str
    ) -> None:
        """
        Enviar mensaje a sala
        
        Args:
            message: Mensaje a enviar
            room: ID de la sala
        """
        if room in self.room_users:
            for user_id in self.room_users[room]:
                await self.send_personal_message(message, user_id)
    
    async def broadcast_to_users(
        self,
        message: Dict[str, Any],
        user_ids: List[str]
    ) -> None:
        """
        Enviar mensaje a usuarios
        
        Args:
            message: Mensaje a enviar
            user_ids: IDs de usuarios
        """
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    def get_room_users(
        self,
        room: str
    ) -> List[str]:
        """
        Obtener usuarios en sala
        
        Args:
            room: ID de la sala
        
        Returns:
            List[str]: IDs de usuarios
        """
        return list(self.room_users.get(room, set()))
    
    def get_user_rooms(
        self,
        user_id: str
    ) -> List[str]:
        """
        Obtener salas de usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            List[str]: IDs de salas
        """
        return list(self.user_rooms.get(user_id, set()))
    
    def get_connected_users(self) -> List[str]:
        """
        Obtener usuarios conectados
        
        Returns:
            List[str]: IDs de usuarios
        """
        return list(self.active_connections.keys())

# Instancia global
manager = ConnectionManager()

# Eventos WebSocket
class WebSocketEvents:
    """Eventos WebSocket"""
    
    # Eventos de conexión
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Eventos de sala
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    
    # Eventos de mensaje
    MESSAGE = "message"
    TYPING = "typing"
    READ = "read"
    
    # Eventos de usuario
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    
    # Eventos de viaje
    TRAVEL_UPDATE = "travel_update"
    TRAVEL_INVITATION = "travel_invitation"
    
    # Eventos de chat
    CHAT_MESSAGE = "chat_message"
    CHAT_TYPING = "chat_typing"
    CHAT_READ = "chat_read"
    
    # Eventos de archivo
    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"
    FILE_SHARE = "file_share"
    
    # Eventos de notificación
    NOTIFICATION = "notification"
    NOTIFICATION_READ = "notification_read"
    
    # Eventos de sistema
    SYSTEM_MESSAGE = "system_message"
    SYSTEM_ERROR = "system_error"

async def handle_websocket(
    websocket: WebSocket,
    connection_type: str,
    user_id: Optional[str] = None
) -> None:
    """
    Manejar conexión WebSocket
    
    Args:
        websocket: Conexión WebSocket
        connection_type: Tipo de conexión
        user_id: ID del usuario
    """
    try:
        await manager.connect(websocket, user_id)
        while True:
            try:
                data = await websocket.receive_text()
                # TODO: Implementar lógica de manejo de mensajes
            except WebSocketDisconnect:
                manager.disconnect(websocket, user_id)
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        manager.disconnect(websocket, user_id) 