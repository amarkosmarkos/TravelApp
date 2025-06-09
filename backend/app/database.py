from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
from .config import settings
from .utils.logging import logger

# Cliente MongoDB
client: Optional[AsyncIOMotorClient] = None

# Instancia de la base de datos
db = None

async def connect_to_mongodb():
    """Conecta a la base de datos MongoDB."""
    global client, db
    try:
        # Asegurar que la URL no termine en '/'
        mongodb_url = settings.MONGODB_URL.rstrip('/')
        client = AsyncIOMotorClient(mongodb_url)
        # Verificar la conexión
        await client.admin.command('ping')
        db = client[settings.DATABASE_NAME]
        logger.info("Conexión exitosa a MongoDB")
    except Exception as e:
        logger.error(f"Error al conectar a MongoDB: {str(e)}")
        raise

async def close_mongodb_connection():
    """Cierra la conexión a MongoDB."""
    global client
    if client:
        client.close()
        logger.info("Conexión a MongoDB cerrada")

async def get_database():
    """Obtiene la instancia de la base de datos."""
    if not client:
        raise RuntimeError("La conexión a MongoDB no está inicializada")
    return client[settings.DATABASE_NAME]

# Funciones para obtener colecciones
async def get_users_collection():
    """Obtiene la colección de usuarios."""
    database = await get_database()
    return database.users

async def get_travels_collection():
    """Obtiene la colección de viajes."""
    database = await get_database()
    return database.travels

def get_chats_collection():
    """Obtiene la colección de chats."""
    return get_database().chats

async def get_messages_collection():
    """Obtiene la colección de mensajes."""
    database = await get_database()
    return database.messages

def get_chat_messages_collection():
    """Obtiene la colección de mensajes de chat."""
    return get_database().chat_messages

async def get_notifications_collection():
    """Obtiene la colección de notificaciones."""
    database = await get_database()
    return database.notifications

def get_files_collection():
    """Obtiene la colección de archivos."""
    return get_database().files

def get_events_collection():
    """Obtiene la colección de eventos."""
    return get_database().events

def get_tasks_collection():
    """Obtiene la colección de tareas."""
    return get_database().tasks

def get_rooms_collection():
    """Obtiene la colección de salas."""
    return get_database().rooms

def get_room_messages_collection():
    """Obtiene la colección de mensajes de sala."""
    return get_database().room_messages

def get_room_participants_collection():
    """Obtiene la colección de participantes de sala."""
    return get_database().room_participants

def get_room_events_collection():
    """Obtiene la colección de eventos de sala."""
    return get_database().room_events

def get_room_files_collection():
    """Obtiene la colección de archivos de sala."""
    return get_database().room_files

def get_room_notifications_collection():
    """Obtiene la colección de notificaciones de sala."""
    return get_database().room_notifications

def get_room_tasks_collection():
    """Obtiene la colección de tareas de sala."""
    return get_database().room_tasks

def get_room_events_history_collection():
    """Obtiene la colección de historial de eventos de sala."""
    return get_database().room_events_history

def get_room_messages_history_collection():
    """Obtiene la colección de historial de mensajes de sala."""
    return get_database().room_messages_history

def get_room_files_history_collection():
    """Obtiene la colección de historial de archivos de sala."""
    return get_database().room_files_history

def get_room_notifications_history_collection():
    """Obtiene la colección de historial de notificaciones de sala."""
    return get_database().room_notifications_history

def get_room_tasks_history_collection():
    """Obtiene la colección de historial de tareas de sala."""
    return get_database().room_tasks_history

def get_room_participants_history_collection():
    """Obtiene la colección de historial de participantes de sala."""
    return get_database().room_participants_history

def get_room_events_history_by_type_collection():
    """Obtiene la colección de historial de eventos de sala por tipo."""
    return get_database().room_events_history_by_type

def get_room_messages_history_by_type_collection():
    """Obtiene la colección de historial de mensajes de sala por tipo."""
    return get_database().room_messages_history_by_type

def get_room_files_history_by_type_collection():
    """Obtiene la colección de historial de archivos de sala por tipo."""
    return get_database().room_files_history_by_type

def get_room_notifications_history_by_type_collection():
    """Obtiene la colección de historial de notificaciones de sala por tipo."""
    return get_database().room_notifications_history_by_type

def get_room_tasks_history_by_type_collection():
    """Obtiene la colección de historial de tareas de sala por tipo."""
    return get_database().room_tasks_history_by_type

def get_room_participants_history_by_type_collection():
    """Obtiene la colección de historial de participantes de sala por tipo."""
    return get_database().room_participants_history_by_type

def get_room_events_history_by_user_collection():
    """Obtiene la colección de historial de eventos de sala por usuario."""
    return get_database().room_events_history_by_user

def get_room_messages_history_by_user_collection():
    """Obtiene la colección de historial de mensajes de sala por usuario."""
    return get_database().room_messages_history_by_user

def get_room_files_history_by_user_collection():
    """Obtiene la colección de historial de archivos de sala por usuario."""
    return get_database().room_files_history_by_user

def get_room_notifications_history_by_user_collection():
    """Obtiene la colección de historial de notificaciones de sala por usuario."""
    return get_database().room_notifications_history_by_user

def get_room_tasks_history_by_user_collection():
    """Obtiene la colección de historial de tareas de sala por usuario."""
    return get_database().room_tasks_history_by_user

def get_room_participants_history_by_user_collection():
    """Obtiene la colección de historial de participantes de sala por usuario."""
    return get_database().room_participants_history_by_user

def get_room_events_history_by_date_collection():
    """Obtiene la colección de historial de eventos de sala por fecha."""
    return get_database().room_events_history_by_date

def get_room_messages_history_by_date_collection():
    """Obtiene la colección de historial de mensajes de sala por fecha."""
    return get_database().room_messages_history_by_date

def get_room_files_history_by_date_collection():
    """Obtiene la colección de historial de archivos de sala por fecha."""
    return get_database().room_files_history_by_date

def get_room_notifications_history_by_date_collection():
    """Obtiene la colección de historial de notificaciones de sala por fecha."""
    return get_database().room_notifications_history_by_date

def get_room_tasks_history_by_date_collection():
    """Obtiene la colección de historial de tareas de sala por fecha."""
    return get_database().room_tasks_history_by_date

def get_room_participants_history_by_date_collection():
    """Obtiene la colección de historial de participantes de sala por fecha."""
    return get_database().room_participants_history_by_date

def get_room_events_history_by_type_and_user_collection():
    """Obtiene la colección de historial de eventos de sala por tipo y usuario."""
    return get_database().room_events_history_by_type_and_user

def get_room_messages_history_by_type_and_user_collection():
    """Obtiene la colección de historial de mensajes de sala por tipo y usuario."""
    return get_database().room_messages_history_by_type_and_user

def get_room_files_history_by_type_and_user_collection():
    """Obtiene la colección de historial de archivos de sala por tipo y usuario."""
    return get_database().room_files_history_by_type_and_user

def get_room_notifications_history_by_type_and_user_collection():
    """Obtiene la colección de historial de notificaciones de sala por tipo y usuario."""
    return get_database().room_notifications_history_by_type_and_user

def get_room_tasks_history_by_type_and_user_collection():
    """Obtiene la colección de historial de tareas de sala por tipo y usuario."""
    return get_database().room_tasks_history_by_type_and_user

def get_room_participants_history_by_type_and_user_collection():
    """Obtiene la colección de historial de participantes de sala por tipo y usuario."""
    return get_database().room_participants_history_by_type_and_user

def get_room_events_history_by_type_and_date_collection():
    """Obtiene la colección de historial de eventos de sala por tipo y fecha."""
    return get_database().room_events_history_by_type_and_date

def get_room_messages_history_by_type_and_date_collection():
    """Obtiene la colección de historial de mensajes de sala por tipo y fecha."""
    return get_database().room_messages_history_by_type_and_date

def get_room_files_history_by_type_and_date_collection():
    """Obtiene la colección de historial de archivos de sala por tipo y fecha."""
    return get_database().room_files_history_by_type_and_date

def get_room_notifications_history_by_type_and_date_collection():
    """Obtiene la colección de historial de notificaciones de sala por tipo y fecha."""
    return get_database().room_notifications_history_by_type_and_date

def get_room_tasks_history_by_type_and_date_collection():
    """Obtiene la colección de historial de tareas de sala por tipo y fecha."""
    return get_database().room_tasks_history_by_type_and_date

def get_room_participants_history_by_type_and_date_collection():
    """Obtiene la colección de historial de participantes de sala por tipo y fecha."""
    return get_database().room_participants_history_by_type_and_date

def get_room_events_history_by_user_and_date_collection():
    """Obtiene la colección de historial de eventos de sala por usuario y fecha."""
    return get_database().room_events_history_by_user_and_date

def get_room_messages_history_by_user_and_date_collection():
    """Obtiene la colección de historial de mensajes de sala por usuario y fecha."""
    return get_database().room_messages_history_by_user_and_date

def get_room_files_history_by_user_and_date_collection():
    """Obtiene la colección de historial de archivos de sala por usuario y fecha."""
    return get_database().room_files_history_by_user_and_date

def get_room_notifications_history_by_user_and_date_collection():
    """Obtiene la colección de historial de notificaciones de sala por usuario y fecha."""
    return get_database().room_notifications_history_by_user_and_date

def get_room_tasks_history_by_user_and_date_collection():
    """Obtiene la colección de historial de tareas de sala por usuario y fecha."""
    return get_database().room_tasks_history_by_user_and_date

def get_room_participants_history_by_user_and_date_collection():
    """Obtiene la colección de historial de participantes de sala por usuario y fecha."""
    return get_database().room_participants_history_by_user_and_date

def get_room_events_history_by_type_and_user_and_date_collection():
    """Obtiene la colección de historial de eventos de sala por tipo, usuario y fecha."""
    return get_database().room_events_history_by_type_and_user_and_date

def get_room_messages_history_by_type_and_user_and_date_collection():
    """Obtiene la colección de historial de mensajes de sala por tipo, usuario y fecha."""
    return get_database().room_messages_history_by_type_and_user_and_date

def get_room_files_history_by_type_and_user_and_date_collection():
    """Obtiene la colección de historial de archivos de sala por tipo, usuario y fecha."""
    return get_database().room_files_history_by_type_and_user_and_date

def get_room_notifications_history_by_type_and_user_and_date_collection():
    """Obtiene la colección de historial de notificaciones de sala por tipo, usuario y fecha."""
    return get_database().room_notifications_history_by_type_and_user_and_date

def get_room_tasks_history_by_type_and_user_and_date_collection():
    """Obtiene la colección de historial de tareas de sala por tipo, usuario y fecha."""
    return get_database().room_tasks_history_by_type_and_user_and_date

def get_room_participants_history_by_type_and_user_and_date_collection():
    """Obtiene la colección de historial de participantes de sala por tipo, usuario y fecha."""
    return get_database().room_participants_history_by_type_and_user_and_date

def get_itineraries_collection():
    """Obtiene la colección de itinerarios."""
    return get_database().itineraries

def get_itinerary_items_collection():
    """Obtiene la colección de items de itinerario."""
    return get_database().itinerary_items

async def get_visits_collection():
    """Obtiene la colección de visitas."""
    database = await get_database()
    return database.visits

def get_places_collection():
    """Obtiene la colección de lugares."""
    return get_database().places

def get_flights_collection():
    """Obtiene la colección de vuelos."""
    return get_database().flights

def get_conversations_collection():
    """Obtiene la colección de conversaciones."""
    return get_database().conversations 