from fastapi import APIRouter, Depends, HTTPException, Request, status, WebSocket, WebSocketDisconnect, Query
from app.services.chat_service import chat_service
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
    get_messages_collection,
    get_database,
    get_users_collection,
    get_cities_collection
)
from ..models.travel import (
    Travel, TravelCreate, TravelUpdate,
    Chat, ChatCreate,
    ChatMessage, ChatMessageCreate,
    Itinerary, ItineraryCreate,
    Visit, VisitCreate,
    Place, PlaceCreate,
    Flight, FlightCreate,
    Message, MessageCreate
)
from app.dependencies import get_current_active_user
from ..models.user import User
from bson import ObjectId
from datetime import datetime
import uuid
import asyncio
import logging
import json
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.crud import travel as travel_crud
import jwt
from jwt.exceptions import InvalidTokenError
from app.config import settings
from ..middleware.auth import get_current_user, verify_ws_token, verify_travel_access
from app.services.hotel_suggestions_service import hotel_suggestions_service

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
async def process_travel_request(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        body = await request.json()
        travel_request = TravelRequest(**body)
        
        # Procesar el mensaje con el servicio de chat
        response = await chat_service.process_message(
            message=travel_request.message,
            user_id=str(current_user.id),
            travel_id=body.get("travel_id"),
            db=db
        )
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

# Chat endpoints
@router.get("/api/travels/{travel_id}/chat", response_model=List[Message])
async def get_chat_messages(
    travel_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    skip: int = 0,
    limit: int = 50
):
    """
    Obtiene los mensajes de un chat específico.
    """
    try:
        messages = await chat_service.get_chat_messages(
            travel_id=travel_id,
            user_id=str(current_user.id),
            db=db,
            skip=skip,
            limit=limit
        )
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting chat messages"
        )

@router.post("/api/travels/{travel_id}/chat", response_model=Message)
async def create_chat_message(
    travel_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Crea un nuevo mensaje en el chat.
    """
    try:
        created_message = await chat_service.create_message(
            db=db,
            travel_id=travel_id,
            user_id=str(current_user.id),
            message=message
        )
        return created_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating chat message"
        )

@router.post("/{travel_id}/chat/process", response_model=dict)
async def process_chat_message(
    travel_id: str,
    request: TravelRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Procesa un mensaje del usuario y genera una respuesta del asistente.
    """
    try:
        response = await chat_service.process_message(
            travel_id=travel_id,
            user_id=str(current_user.id),
            message=request.message,
            db=db
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing chat message"
        )

# Itinerary Items
@router.get("/{travel_id}/itinerary")
async def read_itinerary_items(
    travel_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Fetching itinerary for travel {travel_id} user {current_user.id}")
        travels = await get_travels_collection()
        travel = await travels.find_one({"_id": ObjectId(travel_id)})
        
        if travel is None:
            raise HTTPException(status_code=404, detail="Travel not found")
        if travel["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to access this itinerary")
        
        itineraries = await get_itineraries_collection()
        cursor = itineraries.find({"travel_id": travel_id}).skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            safe = {}
            for k, v in doc.items():
                if k == "_id":
                    safe["id"] = str(v)
                elif hasattr(v, "isoformat"):
                    safe[k] = v.isoformat()
                else:
                    safe[k] = v

            # Normalizar coordenadas de ciudades dentro del itinerario
            cities = safe.get("cities") or []
            normalized_cities = []
            for city in cities:
                try:
                    # Leer de múltiples fuentes: coordinates | latitude/longitude | lat/lon | metadata
                    lat = None
                    lon = None
                    if isinstance(city.get("coordinates"), dict):
                        lat = city["coordinates"].get("latitude") or city["coordinates"].get("lat")
                        lon = city["coordinates"].get("longitude") or city["coordinates"].get("lon")
                    if lat is None and (city.get("latitude") is not None or city.get("longitude") is not None):
                        lat = city.get("latitude")
                        lon = city.get("longitude")
                    if lat is None and (city.get("lat") is not None or city.get("lon") is not None):
                        lat = city.get("lat")
                        lon = city.get("lon")
                    if lat is None and isinstance(city.get("metadata"), dict):
                        lat = city["metadata"].get("latitude")
                        lon = city["metadata"].get("longitude")

                    # Convertir strings a float
                    def _to_float(x):
                        try:
                            return float(x)
                        except Exception:
                            return None

                    lat_f = _to_float(lat)
                    lon_f = _to_float(lon)

                    city_out = dict(city)
                    if lat_f is not None and lon_f is not None:
                        city_out["coordinates"] = {"latitude": lat_f, "longitude": lon_f}
                        # Mantener también campos estándar
                        city_out["latitude"] = lat_f
                        city_out["longitude"] = lon_f
                    normalized_cities.append(city_out)
                except Exception:
                    normalized_cities.append(city)

            safe["cities"] = normalized_cities
            results.append(safe)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching itinerary: {e}")
        raise HTTPException(status_code=500, detail="Failed to load itinerary")

@router.post("/{travel_id}/itinerary", response_model=Itinerary)
async def create_or_update_itinerary_endpoint(
    travel_id: str,
    item: ItineraryCreate,
    current_user: User = Depends(get_current_active_user)
):
    travels = await get_travels_collection()
    travel = await travels.find_one({"_id": ObjectId(travel_id)})
    if travel is None:
        raise HTTPException(status_code=404, detail="Travel not found")
    if travel["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to create items for this travel")
    item_dict = item.dict()
    item_dict["travel_id"] = travel_id
    from app.crud import travel as travel_crud
    itinerary = await travel_crud.create_or_update_itinerary(ItineraryCreate(**item_dict))
    return itinerary

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
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    skip: int = 0,
    limit: int = 50
):
    try:
        logger.info(f"Obteniendo mensajes para viaje {travel_id}")
        
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
                detail="Travel not found"
            )

        # Obtener o crear la conversación para este viaje
        conversations = await get_chats_collection()
        conversation = await conversations.find_one({"travel_id": travel_id})
        
        if not conversation:
            logger.info(f"Creando nueva conversación para viaje {travel_id}")
            # Crear nueva conversación si no existe
            conversation = {
                "travel_id": travel_id,
                "user_id": str(current_user.id),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await conversations.insert_one(conversation)
            conversation["_id"] = result.inserted_id
            logger.info(f"Conversación creada: {conversation['_id']}")

        # Obtener los mensajes de la conversación
        messages = await get_messages_collection()
        cursor = messages.find({
            "conversation_id": str(conversation["_id"]),
            "travel_id": travel_id
        }).sort("timestamp", -1).skip(skip).limit(limit)
        
        message_list = [Message(**doc) async for doc in cursor]
        logger.info(f"Encontrados {len(message_list)} mensajes")
        
        # Invertir la lista para mostrar los mensajes en orden cronológico
        message_list.reverse()
        
        return message_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting messages: {str(e)}"
        )

@router.post("/{travel_id}/messages", response_model=Message)
async def create_travel_message(
    travel_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        created_message = await chat_service.create_message(
            travel_id=travel_id,
            user_id=str(current_user.id),
            content=message.message,
            is_user=message.is_user,
            db=db
        )
        return created_message
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating message")

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

# WebSocket endpoint
@router.websocket("/{travel_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    travel_id: str,
    token: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        # Verificar token y obtener user_id
        user_id = await verify_ws_token(token)
        if not user_id:
            await websocket.close(code=4001)
            return

        # Verificar acceso al viaje
        if not await verify_travel_access(travel_id, user_id, db):
            await websocket.close(code=4004)
            return

        # Aceptar conexión WebSocket
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user {user_id} and travel {travel_id}")

        # Agregar conexión a la lista de conexiones activas
        if travel_id not in active_connections:
            active_connections[travel_id] = set()
        active_connections[travel_id].add(websocket)

        try:
            while True:
                # Recibir mensaje
                data = await websocket.receive_text()
                message_data = json.loads(data)
                logger.info(f"Received message: {message_data}")

                # Extraer el mensaje del usuario
                payload = message_data.get("data", {})
                user_message = payload.get("message", "")
                correlation_id = payload.get("correlation_id") or str(uuid.uuid4())
                if not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "data": {
                            "message": "Mensaje vacío recibido",
                            "is_user": False
                        }
                    })
                    continue

                # Procesar mensaje usando el servicio de chat
                response = await chat_service.process_message(
                    message=user_message,
                    user_id=user_id,
                    travel_id=travel_id,
                    db=db
                )

                # Formatear respuesta para WebSocket
                websocket_response = {
                    "type": "message",
                    "data": {
                        "content": response.get("message", "No se pudo procesar el mensaje"),
                        "is_user": False,
                        "intention": response.get("intention", "unknown"),
                        "classification": {
                            "type": str(response.get("classification", {}).get("type", "unknown")),
                            "confidence": float(response.get("classification", {}).get("confidence", 0.0)),
                            "reason": response.get("classification", {}).get("reason", ""),
                            "extracted_country": response.get("classification", {}).get("extracted_country", "")
                        },
                        "correlation_id": correlation_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "travel_id": travel_id,
                        "user_id": user_id
                    }
                }

                # Si la respuesta fue marcada como duplicada, no enviar nada
                if websocket_response["data"]["intention"] == "duplicate_ignored" or not websocket_response["data"]["content"]:
                    logger.info("Respuesta duplicada/neutra detectada: no se envía por WS")
                    continue

                # Enviar respuesta a todos los clientes, incluido el emisor, con timeout y en paralelo
                targets = list(active_connections.get(travel_id, []))
                if not targets:
                    targets = [websocket]

                logger.info(f"Enviando broadcast a {len(targets)} clientes (incluye emisor)")

                # Serialización segura (Enums → string)
                safe_text = json.dumps(
                    websocket_response,
                    default=lambda o: getattr(o, 'value', str(o))
                )

                async def _safe_send(ws):
                    try:
                        await asyncio.wait_for(ws.send_text(safe_text), timeout=2.0)
                        logger.info("Mensaje enviado exitosamente a cliente")
                    except Exception as e:
                        logger.error(f"Error enviando mensaje por WebSocket: {e}")
                        # Remover conexión fallida
                        try:
                            active_connections[travel_id].discard(ws)
                        except Exception:
                            pass

                await asyncio.gather(*[ _safe_send(ws) for ws in targets ], return_exceptions=True)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id} and travel {travel_id}")
        finally:
            # Remover conexión de la lista de conexiones activas
            if travel_id in active_connections:
                active_connections[travel_id].remove(websocket)
                if not active_connections[travel_id]:
                    del active_connections[travel_id]

    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except:
            pass

@router.get("/{travel_id}/chat", response_model=List[Message])
async def get_chat_messages(
    travel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    skip: int = 0,
    limit: int = 50
):
    """
    Obtiene los mensajes de un chat específico.
    """
    try:
        return await chat_service.get_chat_messages(
            travel_id=travel_id,
            user_id=str(current_user.id),
            db=db,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{travel_id}/chat", response_model=Message)
async def create_chat_message(
    travel_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Crea un nuevo mensaje en un chat.
    """
    try:
        return await chat_service.create_message(
            db=db,
            travel_id=travel_id,
            user_id=str(current_user.id),
            message=message
        )
    except Exception as e:
        logger.error(f"Error creating chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/{travel_id}/itinerary/ai-create")
async def create_itinerary_with_ai_matching(
    travel_id: str,
    ai_cities: List[str],
    country_code: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Crea un itinerario usando IA para hacer match entre ciudades sugeridas y sitios en BD
    """
    try:
        # Verificar que el travel existe y pertenece al usuario
        travels = await get_travels_collection()
        travel = await travels.find_one({"_id": ObjectId(travel_id)})
        if travel is None:
            raise HTTPException(status_code=404, detail="Travel not found")
        if travel["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized for this travel")

        # Obtener todos los sitios disponibles del país específico
        from app.database import get_sites_collection
        sites_collection = await get_sites_collection()
        available_sites = await sites_collection.find(
            {
                "entity_type": "site",
                "subtype": "city",
                "hierarchy": {"$regex": f"^{country_code}", "$options": "i"}
            }, 
            {
                "name": 1, 
                "_id": 1, 
                "normalized_name": 1, 
                "description": 1,
                "lat": 1,
                "lon": 1,
                "hierarchy": 1
            }
        ).to_list(length=None)

        logger.info(f"Found {len(available_sites)} sites for country code {country_code}")

        # Usar IA para hacer match
        from app.services.ai_matching_service import ai_matching_service
        matching_result = await ai_matching_service.match_cities_with_sites(
            ai_cities, 
            available_sites
        )

        # Crear itinerario con las ciudades que hicieron match
        if matching_result.get("matched_cities"):
            itinerary_result = await ai_matching_service.create_itinerary_from_sites(
                matching_result["matched_cities"],
                travel_id,
                str(current_user.id)
            )

            return {
                "success": True,
                "itinerary": itinerary_result["itinerary"],
                "matching_result": matching_result,
                "message": f"Itinerary created with {len(matching_result['matched_cities'])} cities for country {country_code}"
            }
        else:
            return {
                "success": False,
                "message": f"No cities matched with database for country {country_code}",
                "matching_result": matching_result
            }

    except Exception as e:
        logger.error(f"Error creating itinerary with AI matching: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating itinerary: {str(e)}"
        )

@router.get("/sites/available")
async def get_available_sites(
    current_user: User = Depends(get_current_active_user),
    country_code: Optional[str] = None
):
    """
    Obtiene todos los sitios disponibles en la base de datos filtrados por país
    """
    try:
        from app.database import get_sites_collection
        sites_collection = await get_sites_collection()
        
        # Construir query
        query = {
            "entity_type": "site",
            "subtype": "city"
        }
        
        if country_code:
            # Filtrar por código de país en la jerarquía
            query["hierarchy"] = {"$regex": f"^{country_code}", "$options": "i"}
        
        sites = await sites_collection.find(
            query, 
            {
                "name": 1, 
                "_id": 1, 
                "normalized_name": 1, 
                "description": 1,
                "lat": 1,
                "lon": 1,
                "hierarchy": 1
            }
        ).to_list(length=None)
        
        return {
            "available_sites": sites,
            "total_count": len(sites),
            "country_code": country_code
        }
    except Exception as e:
        logger.error(f"Error getting available sites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los sitios disponibles"
        ) 

@router.get("/{travel_id}/hotels/suggestions")
async def get_hotel_suggestions(
    travel_id: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        travels = await get_travels_collection()
        travel = await travels.find_one({"_id": ObjectId(travel_id)})
        if travel is None:
            raise HTTPException(status_code=404, detail="Travel not found")
        if travel.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized for this travel")

        # Intentar servir desde BBDD primero
        itineraries = await get_itineraries_collection()
        it = await itineraries.find_one({"travel_id": travel_id})
        if it and it.get("hotel_suggestions"):
            return {"travel_id": travel_id, "suggestions": it.get("hotel_suggestions")}

        # Si no hay, generar on-demand y devolver
        suggestions = await hotel_suggestions_service.get_suggestions_for_travel(travel_id)
        # Guardar asincrónicamente (no bloquear respuesta)
        try:
            await itineraries.update_one(
                {"travel_id": travel_id},
                {"$set": {"hotel_suggestions": suggestions, "hotel_suggestions_generated_at": datetime.utcnow().isoformat()}}
            )
        except Exception:
            pass
        return {"travel_id": travel_id, "suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hotel suggestions: {e}")
        raise HTTPException(status_code=500, detail="Error getting hotel suggestions")

@router.post("/country-code")
async def get_country_code(
    country_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el código de país ISO a partir del nombre del país
    """
    try:
        # Mapeo simple de países a códigos ISO
        country_mapping = {
            "thailand": "TH",
            "japan": "JP", 
            "spain": "ES",
            "france": "FR",
            "italy": "IT",
            "germany": "DE",
            "united kingdom": "GB",
            "uk": "GB",
            "england": "GB",
            "usa": "US",
            "united states": "US",
            "america": "US",
            "china": "CN",
            "south korea": "KR",
            "korea": "KR",
            "australia": "AU",
            "canada": "CA",
            "brazil": "BR",
            "argentina": "AR",
            "mexico": "MX",
            "peru": "PE",
            "chile": "CL",
            "colombia": "CO",
            "venezuela": "VE",
            "ecuador": "EC",
            "bolivia": "BO",
            "paraguay": "PY",
            "uruguay": "UY",
            "guyana": "GY",
            "suriname": "SR",
            "french guiana": "GF"
        }
        
        country_code = country_mapping.get(country_name.lower().strip(), "TH")
        
        return {
            "country_name": country_name,
            "country_code": country_code,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting country code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting country code: {str(e)}"
        ) 