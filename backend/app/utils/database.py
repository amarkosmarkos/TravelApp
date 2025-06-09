from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    """Clase para manejo de base de datos"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Conectar a la base de datos"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            await self.create_indexes()
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Cerrar conexión a la base de datos"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def get_database(self) -> AsyncIOMotorDatabase:
        """
        Obtener instancia de base de datos
        
        Returns:
            AsyncIOMotorDatabase: Instancia de base de datos
        """
        if self.db is None:
            await self.connect()
        return self.db
    
    async def create_indexes(self) -> None:
        """Crear índices de base de datos"""
        # Índices para usuarios
        await self.db.users.create_index("email", unique=True)
        await self.db.users.create_index("full_name")
        await self.db.users.create_index("roles")
        await self.db.users.create_index("is_active")
        
        # Índices para viajes
        await self.db.travels.create_index("user_id")
        await self.db.travels.create_index("status")
        await self.db.travels.create_index("created_at")
        
        # Índices para mensajes
        await self.db.messages.create_index("travel_id")
        await self.db.messages.create_index("user_id")
        await self.db.messages.create_index("created_at")
        
        # Índices para notificaciones
        await self.db.notifications.create_index("user_id")
        await self.db.notifications.create_index("read")
        await self.db.notifications.create_index("created_at")
        
        logger.info("Database indexes created")

def format_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatear documento de MongoDB
    
    Args:
        document: Documento de MongoDB
    
    Returns:
        Dict[str, Any]: Documento formateado
    """
    if not document:
        return {}
    
    # Convertir ObjectId a string
    if "_id" in document:
        document["_id"] = str(document["_id"])
    
    # Convertir fechas a ISO
    for key, value in document.items():
        if isinstance(value, datetime):
            document[key] = value.isoformat()
    
    return document

def parse_object_id(id_str: str) -> ObjectId:
    """
    Convertir string a ObjectId
    
    Args:
        id_str: ID en formato string
    
    Returns:
        ObjectId: ID en formato ObjectId
    
    Raises:
        ValueError: Si el ID no es válido
    """
    try:
        return ObjectId(id_str)
    except Exception as e:
        raise ValueError(f"Invalid ObjectId: {str(e)}")

def build_query(
    filters: Dict[str, Any],
    search_fields: Optional[List[str]] = None,
    search_term: Optional[str] = None
) -> Dict[str, Any]:
    """
    Construir query de MongoDB
    
    Args:
        filters: Filtros a aplicar
        search_fields: Campos para búsqueda
        search_term: Término de búsqueda
    
    Returns:
        Dict[str, Any]: Query de MongoDB
    """
    query = {}
    
    # Aplicar filtros
    for key, value in filters.items():
        if value is not None:
            query[key] = value
    
    # Aplicar búsqueda
    if search_term and search_fields:
        search_query = []
        for field in search_fields:
            search_query.append({field: {"$regex": search_term, "$options": "i"}})
        if search_query:
            query["$or"] = search_query
    
    return query

# Instancia global de base de datos
db = Database()

# Funciones para obtener colecciones
async def get_users_collection():
    """Obtener colección de usuarios"""
    database = await db.get_database()
    return database.users

async def get_travels_collection():
    """Obtener colección de viajes"""
    database = await db.get_database()
    return database.travels

async def get_messages_collection():
    """Obtener colección de mensajes"""
    database = await db.get_database()
    return database.messages

async def get_notifications_collection():
    """Obtener colección de notificaciones"""
    database = await db.get_database()
    return database.notifications

# Alias para compatibilidad
users_collection = get_users_collection
travels_collection = get_travels_collection
messages_collection = get_messages_collection
notifications_collection = get_notifications_collection 