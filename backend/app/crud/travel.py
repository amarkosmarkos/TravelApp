from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from ..database import (
    get_travels_collection,
    get_chats_collection,
    get_chat_messages_collection,
    get_itineraries_collection,
    get_itinerary_items_collection,
    get_visits_collection,
    get_places_collection,
    get_flights_collection,
    get_messages_collection,
    get_conversations_collection
)
from ..models.travel import TravelCreate, Travel, ChatCreate, Chat, ChatMessageCreate, ChatMessage, ItineraryCreate, Itinerary, VisitCreate, Visit, PlaceCreate, Place, FlightCreate, Flight, TravelUpdate, Message, MessageCreate
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

async def get_travel(db: AsyncIOMotorDatabase, travel_id: str) -> Optional[Travel]:
    travels = await get_travels_collection()
    travel = await travels.find_one({"_id": ObjectId(travel_id)})
    if travel:
        return Travel(**travel)
    return None

async def get_travels(
    db: AsyncIOMotorDatabase,
    user_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Travel]:
    travels = get_travels_collection()
    cursor = travels.find({"user_id": user_id}).skip(skip).limit(limit)
    travels_list = await cursor.to_list(length=limit)
    return [Travel(**travel) for travel in travels_list]

async def create_travel(
    db: AsyncIOMotorDatabase,
    travel: TravelCreate,
    user_id: str
) -> Travel:
    try:
        # Crear el viaje
        travels = await get_travels_collection()
        travel_dict = travel.dict()
        travel_dict["user_id"] = user_id
        travel_dict["created_at"] = datetime.utcnow()
        travel_dict["updated_at"] = datetime.utcnow()
        
        result = await travels.insert_one(travel_dict)
        created_travel = await travels.find_one({"_id": result.inserted_id})
        
        # Crear la conversación inicial
        conversations = await get_chats_collection()
        conversation = {
            "travel_id": str(result.inserted_id),
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        conversation_result = await conversations.insert_one(conversation)
        
        # Crear mensaje de bienvenida
        messages = await get_messages_collection()
        welcome_message = {
            "message": "¡Bienvenido a tu nuevo viaje! ¿A dónde te gustaría ir?",
            "is_user": False,
            "travel_id": str(result.inserted_id),
            "conversation_id": str(conversation_result.inserted_id),
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        }
        await messages.insert_one(welcome_message)
        
        return Travel(**created_travel)
    except Exception as e:
        logger.error(f"Error creating travel: {str(e)}")
        raise

async def update_travel(
    db: AsyncIOMotorDatabase,
    travel_id: str,
    travel: TravelUpdate
) -> Optional[Travel]:
    travels = get_travels_collection()
    update_data = travel.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await travels.update_one(
        {"_id": ObjectId(travel_id)},
        {"$set": update_data}
    )
    
    if result.modified_count:
        updated_travel = await travels.find_one({"_id": ObjectId(travel_id)})
        return Travel(**updated_travel)
    return None

async def delete_travel(db: AsyncIOMotorDatabase, travel_id: str) -> bool:
    travels = get_travels_collection()
    result = await travels.delete_one({"_id": ObjectId(travel_id)})
    return result.deleted_count > 0

# Chat operations
async def get_chat_messages(chat_id: str, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
    chat_messages = get_chat_messages_collection()
    cursor = chat_messages.find({"chat_id": chat_id}).skip(skip).limit(limit)
    return [ChatMessage(**message) async for message in cursor]

async def create_chat_message(message: ChatMessageCreate) -> ChatMessage:
    chat_messages = get_chat_messages_collection()
    message_dict = message.dict()
    message_dict["created_at"] = datetime.utcnow()
    
    result = await chat_messages.insert_one(message_dict)
    created_message = await chat_messages.find_one({"_id": result.inserted_id})
    return ChatMessage(**created_message)

async def create_chat(chat: ChatCreate) -> Chat:
    chats = get_chats_collection()
    chat_dict = chat.dict()
    chat_dict["created_at"] = datetime.utcnow()
    chat_dict["updated_at"] = datetime.utcnow()
    
    result = await chats.insert_one(chat_dict)
    created_chat = await chats.find_one({"_id": result.inserted_id})
    return Chat(**created_chat)

# Itinerary operations
async def get_itinerary_items(itinerary_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    itinerary_items = get_itinerary_items_collection()
    cursor = itinerary_items.find({"itinerary_id": itinerary_id}).skip(skip).limit(limit)
    return [dict(item) async for item in cursor]

async def create_itinerary_item(item: Dict[str, Any]) -> Dict[str, Any]:
    itinerary_items = get_itinerary_items_collection()
    item_dict = item.copy()
    item_dict["created_at"] = datetime.utcnow()
    item_dict["updated_at"] = datetime.utcnow()
    
    result = await itinerary_items.insert_one(item_dict)
    created_item = await itinerary_items.find_one({"_id": result.inserted_id})
    return dict(created_item)

async def create_itinerary(itinerary: ItineraryCreate) -> Itinerary:
    itineraries = get_itineraries_collection()
    itinerary_dict = itinerary.dict()
    itinerary_dict["created_at"] = datetime.utcnow()
    itinerary_dict["updated_at"] = datetime.utcnow()
    
    result = await itineraries.insert_one(itinerary_dict)
    created_itinerary = await itineraries.find_one({"_id": result.inserted_id})
    return Itinerary(**created_itinerary)

# Visit operations
async def get_visits(travel_id: str, skip: int = 0, limit: int = 100) -> List[Visit]:
    visits = get_visits_collection()
    cursor = visits.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [Visit(**visit) async for visit in cursor]

async def create_visit(visit: VisitCreate) -> Visit:
    visits = get_visits_collection()
    visit_dict = visit.dict()
    visit_dict["created_at"] = datetime.utcnow()
    visit_dict["updated_at"] = datetime.utcnow()
    
    result = await visits.insert_one(visit_dict)
    created_visit = await visits.find_one({"_id": result.inserted_id})
    return Visit(**created_visit)

# Place operations
async def get_places(travel_id: str, skip: int = 0, limit: int = 100) -> List[Place]:
    places = get_places_collection()
    cursor = places.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [Place(**place) async for place in cursor]

async def create_place(place: PlaceCreate) -> Place:
    places = get_places_collection()
    place_dict = place.dict()
    place_dict["created_at"] = datetime.utcnow()
    place_dict["updated_at"] = datetime.utcnow()
    
    result = await places.insert_one(place_dict)
    created_place = await places.find_one({"_id": result.inserted_id})
    return Place(**created_place)

# Flight operations
async def get_flights(travel_id: str, skip: int = 0, limit: int = 100) -> List[Flight]:
    flights = get_flights_collection()
    cursor = flights.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [Flight(**flight) async for flight in cursor]

async def create_flight(flight: FlightCreate) -> Flight:
    flights = get_flights_collection()
    flight_dict = flight.dict()
    flight_dict["created_at"] = datetime.utcnow()
    flight_dict["updated_at"] = datetime.utcnow()
    
    result = await flights.insert_one(flight_dict)
    created_flight = await flights.find_one({"_id": result.inserted_id})
    return Flight(**created_flight)

async def get_travel_messages(
    db: AsyncIOMotorDatabase,
    travel_id: str
) -> List[Message]:
    # Primero obtener la conversación asociada al viaje
    conversations = await get_conversations_collection()
    conversation = await conversations.find_one({"travel_id": travel_id})
    
    if not conversation:
        # Si no existe conversación, crearla
        conversation = {
            "travel_id": travel_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await conversations.insert_one(conversation)
        conversation["_id"] = result.inserted_id
    
    # Obtener los mensajes de la conversación
    messages = await get_messages_collection()
    cursor = messages.find({
        "travel_id": travel_id,
        "conversation_id": str(conversation["_id"])
    }).sort("timestamp", 1)
    
    messages_list = await cursor.to_list(length=None)
    return [Message(
        travel_id=msg["travel_id"],
        conversation_id=str(conversation["_id"]),
        message=msg["message"],
        is_user=msg["is_user"],
        timestamp=msg["timestamp"]
    ) for msg in messages_list]

async def create_travel_message(
    db: AsyncIOMotorDatabase,
    travel_id: str,
    message: MessageCreate
) -> Message:
    messages = await get_messages_collection()
    message_dict = message.dict()
    message_dict["created_at"] = datetime.utcnow()
    
    result = await messages.insert_one(message_dict)
    created_message = await messages.find_one({"_id": result.inserted_id})
    return Message(**created_message) 