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

async def get_chats_collection():
    """Obtiene la colección de chats."""
    database = await get_database()
    return database.chats

async def get_messages_collection():
    """Obtiene la colección de mensajes."""
    database = await get_database()
    return database.messages

async def get_chat_messages_collection():
    """Obtiene la colección de mensajes de chat."""
    database = await get_database()
    return database.chat_messages

async def get_notifications_collection():
    """Obtiene la colección de notificaciones."""
    database = await get_database()
    return database.notifications

async def get_files_collection():
    """Obtiene la colección de archivos."""
    database = await get_database()
    return database.files

async def get_events_collection():
    """Obtiene la colección de eventos."""
    database = await get_database()
    return database.events

async def get_tasks_collection():
    """Obtiene la colección de tareas."""
    database = await get_database()
    return database.tasks

async def get_rooms_collection():
    """Obtiene la colección de salas."""
    database = await get_database()
    return database.rooms

async def get_room_messages_collection():
    """Obtiene la colección de mensajes de sala."""
    database = await get_database()
    return database.room_messages

async def get_room_participants_collection():
    """Obtiene la colección de participantes de sala."""
    database = await get_database()
    return database.room_participants

async def get_room_events_collection():
    """Obtiene la colección de eventos de sala."""
    database = await get_database()
    return database.room_events

async def get_room_files_collection():
    """Obtiene la colección de archivos de sala."""
    database = await get_database()
    return database.room_files

async def get_room_notifications_collection():
    """Obtiene la colección de notificaciones de sala."""
    database = await get_database()
    return database.room_notifications

async def get_room_tasks_collection():
    """Obtiene la colección de tareas de sala."""
    database = await get_database()
    return database.room_tasks

async def get_conversations_collection():
    """Obtiene la colección de conversaciones."""
    database = await get_database()
    return database.conversations

async def get_room_events_history_collection():
    """Obtiene la colección de historial de eventos de sala."""
    database = await get_database()
    return database.room_events_history

async def get_room_messages_history_collection():
    """Obtiene la colección de historial de mensajes de sala."""
    database = await get_database()
    return database.room_messages_history

async def get_room_files_history_collection():
    """Obtiene la colección de historial de archivos de sala."""
    database = await get_database()
    return database.room_files_history

async def get_room_notifications_history_collection():
    """Obtiene la colección de historial de notificaciones de sala."""
    database = await get_database()
    return database.room_notifications_history

async def get_room_tasks_history_collection():
    """Obtiene la colección de historial de tareas de sala."""
    database = await get_database()
    return database.room_tasks_history

async def get_room_participants_history_collection():
    """Obtiene la colección de historial de participantes de sala."""
    database = await get_database()
    return database.room_participants_history

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

async def get_itineraries_collection():
    """Obtiene la colección de itinerarios."""
    database = await get_database()
    return database.itineraries

async def get_itinerary_items_collection():
    """Obtiene la colección de items de itinerario."""
    database = await get_database()
    return database.itinerary_items

async def get_visits_collection():
    """Obtiene la colección de visitas."""
    database = await get_database()
    return database.visits

async def get_places_collection():
    """Obtiene la colección de lugares."""
    database = await get_database()
    return database.places

async def get_flights_collection():
    """Obtiene la colección de vuelos."""
    database = await get_database()
    return database.flights 