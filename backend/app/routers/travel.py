from fastapi import APIRouter, Depends, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from app.travel_assistant import travel_assistant
from typing import List, Optional
from pydantic import BaseModel
from app.database import (
    get_travels_collection,
    get_chats_collection,
    get_chat_messages_collection,
    get_itineraries_collection,
    get_itinerary_items_collection,
    get_visits_collection,
    get_places_collection,
    get_flights_collection,
    get_messages_collection
)
from ..models.travel import (
    Travel, TravelCreate, TravelUpdate,
    ChatMessage, ChatMessageCreate,
    ItineraryItem, ItineraryItemCreate,
    Visit, VisitCreate,
    Place, PlaceCreate,
    Flight, FlightCreate,
    Message, MessageCreate
)
from app.dependencies import get_current_active_user
from ..models.user import User
from bson import ObjectId
from datetime import datetime
import logging
import json
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.crud import travel as travel_crud

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["travels"]
)

# Almacenar conexiones WebSocket activas
active_connections: dict = {}

class TravelRequest(BaseModel):
    message: str

class TravelResponse(BaseModel):
    intention: str
    cities: List[dict]
    user_message: str

@router.post("/travel", response_model=TravelResponse)
async def process_travel_request(request: Request, current_user: User = Depends(get_current_active_user)):
    try:
        body = await request.json()
        travel_request = TravelRequest(**body)
        
        # Process the message with the verified user_id
        response = await travel_assistant.process_message(travel_request.message, str(current_user.id))
        return TravelResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing travel request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing travel request: {str(e)}"
        )

@router.get("/", response_model=List[Travel])
async def get_travels(
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 10
):
    try:
        logger.info(f"Obteniendo viajes para usuario {current_user.email}")
        travels = await get_travels_collection()
        cursor = travels.find({"user_id": str(current_user.id)}).skip(skip).limit(limit)
        return [Travel(**doc) async for doc in cursor]
    except Exception as e:
        logger.error(f"Error obteniendo viajes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los viajes"
        )

@router.post("/", response_model=Travel)
async def create_travel(
    travel: TravelCreate,
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Creando nuevo viaje para usuario {current_user.email}")
        travels = await get_travels_collection()
        
        # Crear el documento del viaje
        travel_dict = travel.dict()
        travel_dict["user_id"] = str(current_user.id)
        travel_dict["created_at"] = datetime.utcnow()
        travel_dict["updated_at"] = datetime.utcnow()
        
        # Insertar en la base de datos
        result = await travels.insert_one(travel_dict)
        
        # Obtener el viaje creado
        created_travel = await travels.find_one({"_id": result.inserted_id})
        logger.info(f"Viaje creado exitosamente: {created_travel['_id']}")
        
        return Travel(**created_travel)
    except Exception as e:
        logger.error(f"Error creando viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el viaje"
        )

@router.get("/{travel_id}", response_model=Travel)
async def get_travel(
    travel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Obteniendo viaje {travel_id} para usuario {current_user.email}")
        travels = await get_travels_collection()
        travel = await travels.find_one({
            "_id": ObjectId(travel_id),
            "user_id": str(current_user.id)
        })
        
        if not travel:
            logger.warning(f"Viaje {travel_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
            
        return Travel(**travel)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el viaje"
        )

@router.put("/{travel_id}", response_model=Travel)
async def update_travel(
    travel_id: str,
    travel_update: TravelUpdate,
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Actualizando viaje {travel_id} para usuario {current_user.email}")
        travels = await get_travels_collection()
        
        # Verificar que el viaje existe y pertenece al usuario
        travel = await travels.find_one({
            "_id": ObjectId(travel_id),
            "user_id": str(current_user.id)
        })
        
        if not travel:
            logger.warning(f"Viaje {travel_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
        
        # Preparar la actualización
        update_data = travel_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Actualizar en la base de datos
        await travels.update_one(
            {"_id": ObjectId(travel_id)},
            {"$set": update_data}
        )
        
        # Obtener el viaje actualizado
        updated_travel = await travels.find_one({"_id": ObjectId(travel_id)})
        logger.info(f"Viaje {travel_id} actualizado exitosamente")
        
        return Travel(**updated_travel)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el viaje"
        )

@router.delete("/{travel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel(
    travel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Eliminando viaje {travel_id} para usuario {current_user.email}")
        travels = await get_travels_collection()
        
        # Verificar que el viaje existe y pertenece al usuario
        travel = await travels.find_one({
            "_id": ObjectId(travel_id),
            "user_id": str(current_user.id)
        })
        
        if not travel:
            logger.warning(f"Viaje {travel_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
        
        # Eliminar el viaje y todos sus datos relacionados
        await db.chats().delete_many({"travel_id": travel_id})
        await db.chat_messages().delete_many({"travel_id": travel_id})
        await db.itineraries().delete_many({"travel_id": travel_id})
        await db.itinerary_items().delete_many({"travel_id": travel_id})
        await db.visits().delete_many({"travel_id": travel_id})
        await db.places().delete_many({"travel_id": travel_id})
        await db.flights().delete_many({"travel_id": travel_id})
        await travels.delete_one({"_id": ObjectId(travel_id)})
        
        logger.info(f"Viaje {travel_id} y datos relacionados eliminados exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el viaje"
        )

# Chat Messages
@router.get("/{travel_id}/chat", response_model=List[ChatMessage])
async def get_chat_messages(
    travel_id: str,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50
):
    try:
        logger.info(f"Obteniendo mensajes de chat para viaje {travel_id}")
        chat_messages = await db.chat_messages()
        
        # Verificar que el viaje existe y pertenece al usuario
        travels = await get_travels_collection()
        travel = await travels.find_one({
            "_id": ObjectId(travel_id),
            "user_id": str(current_user.id)
        })
        
        if not travel:
            logger.warning(f"Viaje {travel_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
        
        # Obtener los mensajes
        cursor = chat_messages.find({"travel_id": travel_id}).skip(skip).limit(limit)
        return [ChatMessage(**doc) async for doc in cursor]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo mensajes de chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los mensajes de chat"
        )

@router.post("/{travel_id}/chat", response_model=ChatMessage)
async def create_chat_message(
    travel_id: str,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Creando mensaje de chat para viaje {travel_id}")
        chat_messages = await db.chat_messages()
        
        # Verificar que el viaje existe y pertenece al usuario
        travels = await get_travels_collection()
        travel = await travels.find_one({
            "_id": ObjectId(travel_id),
            "user_id": str(current_user.id)
        })
        
        if not travel:
            logger.warning(f"Viaje {travel_id} no encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
        
        # Crear el mensaje
        chat_message = ChatMessageCreate(
            travel_id=travel_id,
            content=message.content,
            is_user=message.is_user,
            timestamp=datetime.utcnow()
        )
        
        # Insertar en la base de datos
        result = await chat_messages.insert_one(chat_message.dict())
        
        # Obtener el mensaje creado
        created_message = await chat_messages.find_one({"_id": result.inserted_id})
        logger.info(f"Mensaje de chat creado exitosamente: {created_message['_id']}")
        
        return ChatMessage(**created_message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando mensaje de chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el mensaje de chat"
        )

# Itinerary Items
@router.get("/{travel_id}/itinerary", response_model=List[ItineraryItem])
async def read_itinerary_items(
    travel_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this itinerary")
    
    cursor = itinerary_items.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [ItineraryItem(**doc) async for doc in cursor]

@router.post("/{travel_id}/itinerary", response_model=ItineraryItem)
async def create_itinerary_item(
    travel_id: str,
    item: ItineraryItemCreate,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to create items for this travel")
    
    item_dict = item.dict()
    item_dict["travel_id"] = travel_id
    item_dict["created_at"] = datetime.utcnow()
    item_dict["updated_at"] = datetime.utcnow()
    
    result = await itinerary_items.insert_one(item_dict)
    created_item = await itinerary_items.find_one({"_id": result.inserted_id})
    return ItineraryItem(**created_item)

# Visits
@router.get("/{travel_id}/visits", response_model=List[Visit])
async def read_visits(
    travel_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access these visits")
    
    cursor = visits.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [Visit(**doc) async for doc in cursor]

@router.post("/{travel_id}/visits", response_model=Visit)
async def create_visit(
    travel_id: str,
    visit: VisitCreate,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to create visits for this travel")
    
    visit_dict = visit.dict()
    visit_dict["travel_id"] = travel_id
    visit_dict["created_at"] = datetime.utcnow()
    visit_dict["updated_at"] = datetime.utcnow()
    
    result = await visits.insert_one(visit_dict)
    created_visit = await visits.find_one({"_id": result.inserted_id})
    return Visit(**created_visit)

# Places
@router.get("/{travel_id}/places", response_model=List[Place])
async def read_places(
    travel_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access these places")
    
    cursor = places.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [Place(**doc) async for doc in cursor]

@router.post("/{travel_id}/places", response_model=Place)
async def create_place(
    travel_id: str,
    place: PlaceCreate,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to create places for this travel")
    
    place_dict = place.dict()
    place_dict["travel_id"] = travel_id
    place_dict["created_at"] = datetime.utcnow()
    place_dict["updated_at"] = datetime.utcnow()
    
    result = await places.insert_one(place_dict)
    created_place = await places.find_one({"_id": result.inserted_id})
    return Place(**created_place)

# Flights
@router.get("/{travel_id}/flights", response_model=List[Flight])
async def read_flights(
    travel_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access these flights")
    
    cursor = flights.find({"travel_id": travel_id}).skip(skip).limit(limit)
    return [Flight(**doc) async for doc in cursor]

@router.post("/{travel_id}/flights", response_model=Flight)
async def create_flight(
    travel_id: str,
    flight: FlightCreate,
    current_user: User = Depends(get_current_active_user)
):
    travel = await get_travels_collection()
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to create flights for this travel")
    
    flight_dict = flight.dict()
    flight_dict["travel_id"] = travel_id
    flight_dict["created_at"] = datetime.utcnow()
    flight_dict["updated_at"] = datetime.utcnow()
    
    result = await flights.insert_one(flight_dict)
    created_flight = await flights.find_one({"_id": result.inserted_id})
    return Flight(**created_flight)

@router.post("/travel")
async def process_travel_message(
    message: dict,
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Procesar el mensaje y generar una respuesta
        response = {
            "type": "message",
            "data": {
                "message": f"Recibí tu mensaje: {message.get('message', '')}"
            }
        }
        
        # Enviar la respuesta a través de WebSocket si hay una conexión activa
        if message.get('travel_id') in active_connections:
            await active_connections[message['travel_id']].send_text(json.dumps(response))
        
        return response
    except Exception as e:
        logger.error(f"Error processing travel message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing message")

@router.get("/{travel_id}/messages", response_model=List[Message])
async def get_travel_messages(
    travel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    messages = await travel_crud.get_travel_messages(travel_id)
    return messages

@router.post("/{travel_id}/messages", response_model=Message)
async def create_travel_message(
    travel_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user)
):
    # Verificar que el viaje existe y pertenece al usuario
    travel = await travel_crud.get_travel(travel_id)
    if not travel:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this travel")
    
    # Crear el mensaje
    created_message = await travel_crud.create_travel_message(travel_id, message)
    return created_message

@router.get("/", response_model=List[Travel])
async def get_travels(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    travels = await travel_crud.get_travels(current_user.id, skip, limit)
    return travels

@router.post("/", response_model=Travel)
async def create_travel(
    travel: TravelCreate,
    current_user: User = Depends(get_current_active_user)
):
    created_travel = await travel_crud.create_travel(travel, current_user.id)
    return created_travel

@router.get("/{travel_id}", response_model=Travel)
async def get_travel(
    travel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    travel = await travel_crud.get_travel(travel_id)
    if not travel:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this travel")
    return travel

@router.put("/{travel_id}", response_model=Travel)
async def update_travel(
    travel_id: str,
    travel: TravelUpdate,
    current_user: User = Depends(get_current_active_user)
):
    existing_travel = await travel_crud.get_travel(travel_id)
    if not existing_travel:
        raise HTTPException(status_code=404, detail="Travel not found")
    if existing_travel.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this travel")
    
    updated_travel = await travel_crud.update_travel(travel_id, travel)
    return updated_travel

@router.delete("/{travel_id}")
async def delete_travel(
    travel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    existing_travel = await travel_crud.get_travel(travel_id)
    if not existing_travel:
        raise HTTPException(status_code=404, detail="Travel not found")
    if existing_travel.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this travel")
    
    await travel_crud.delete_travel(travel_id)
    return {"message": "Travel deleted successfully"} 