from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import (
    get_database,
    get_chats_collection,
    get_messages_collection,
    get_itineraries_collection,
    get_cities_collection
)
from app.models.travel import Message, MessageCreate, Chat, ChatCreate, ItineraryCreate
from app.crud import travel as travel_crud
from app.travel_assistant import travel_assistant
import logging
from fastapi import HTTPException
from bson import ObjectId

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.assistant = travel_assistant

    async def get_or_create_chat(
        self,
        travel_id: str,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Chat:
        """
        Obtiene o crea un chat para un viaje específico.
        Asegura que solo exista un chat por viaje y que solo el propietario pueda acceder.
        """
        try:
            # Si es el asistente, permitir acceso
            if user_id == "assistant":
                chats = await get_chats_collection()
                chat = await chats.find_one({"travel_id": travel_id})
                if chat:
                    return Chat(**chat)
                # Si no existe el chat, crearlo
                chat_data = ChatCreate(
                    travel_id=travel_id,
                    title=f"Chat for Travel {travel_id}"
                )
                chat_dict = chat_data.dict()
                chat_dict["user_id"] = user_id
                chat_dict["created_at"] = datetime.utcnow()
                chat_dict["updated_at"] = datetime.utcnow()
                result = await chats.insert_one(chat_dict)
                chat = await chats.find_one({"_id": result.inserted_id})
                return Chat(**chat)

            # Para usuarios normales, verificar acceso
            travel = await travel_crud.get_travel(db, travel_id)
            if not travel:
                raise HTTPException(status_code=404, detail="Travel not found")
            if str(travel.user_id) != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to access this travel")

            # Buscar el chat existente para este viaje
            chats = await get_chats_collection()
            chat = await chats.find_one({"travel_id": travel_id})

            if not chat:
                # Crear nuevo chat solo si no existe uno para este viaje
                chat_data = ChatCreate(
                    travel_id=travel_id,
                    title=f"Chat for {travel.title or 'Travel'}"
                )
                chat_dict = chat_data.dict()
                chat_dict["user_id"] = user_id
                chat_dict["created_at"] = datetime.utcnow()
                chat_dict["updated_at"] = datetime.utcnow()
                result = await chats.insert_one(chat_dict)
                chat = await chats.find_one({"_id": result.inserted_id})
                logger.info(f"Created new chat for travel {travel_id} with title {travel.title}")

            return Chat(**chat)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_or_create_chat: {str(e)}")
            raise HTTPException(status_code=500, detail="Error accessing chat")

    async def process_message(
        self,
        travel_id: str,
        user_id: str,
        message: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        """
        try:
            logger.info(f"Procesando mensaje para travel_id={travel_id}, user_id={user_id}")
            
            # Verificar que el viaje existe y pertenece al usuario
            travel = await travel_crud.get_travel(db, travel_id)
            if not travel or str(travel.user_id) != user_id:
                logger.error(f"Travel no encontrado o no autorizado: travel_id={travel_id}, user_id={user_id}")
                raise HTTPException(status_code=404, detail="Travel not found or unauthorized")

            # Guardar mensaje del usuario
            user_message = MessageCreate(
                content=message,
                is_user=True,
                travel_id=travel_id
            )
            saved_user_message = await self.create_message(db, travel_id, user_id, user_message)
            logger.info(f"Mensaje del usuario guardado: {saved_user_message.id}")

            # Obtener historial de mensajes para este viaje
            messages = await get_messages_collection()
            travel_messages = await messages.find(
                {
                    "travel_id": travel_id,
                    "user_id": {"$in": [user_id, "assistant"]}
                }
            ).sort("timestamp", 1).limit(20).to_list(length=None)
            
            logger.info(f"Historial de mensajes obtenido para travel_id={travel_id}: {len(travel_messages)} mensajes")

            # Procesar con el asistente
            try:
                logger.info("Enviando mensaje al asistente")
                response = await self.assistant.process_message(
                    message=message,
                    user_id=user_id,
                    message_history=travel_messages
                )
                logger.info(f"Respuesta del asistente recibida: {response}")
                
                if not response or "message" not in response:
                    logger.error("Respuesta inválida del asistente")
                    assistant_response = "Lo siento, no pude procesar tu mensaje correctamente."
                else:
                    assistant_response = response["message"]

                    # Si la respuesta incluye un itinerario, crear los registros en la base de datos
                    if "cities" in response and response.get("intention") == "itinerary_created":
                        try:
                            # Usar el servicio de AI matching para crear el itinerario con sitios
                            from app.services.ai_matching_service import ai_matching_service
                            
                            # Convertir la respuesta del AI a formato de matched_cities
                            matched_cities = []
                            for city_data in response["cities"]:
                                site_id = city_data.get("id")
                                site_name = city_data.get("name")
                                
                                if site_id:
                                    matched_cities.append({
                                        "ai_name": site_name,
                                        "db_id": site_id,
                                        "db_name": site_name,
                                        "confidence": 1.0  # Alta confianza porque ya viene de la BD
                                    })
                                    logger.info(f"Sitio preparado para itinerario: {site_name} (ID: {site_id})")
                                else:
                                    logger.warning(f"Ciudad sin ID en la respuesta: {site_name}")

                            if matched_cities:
                                # Crear itinerario usando el servicio de AI matching
                                itinerary_result = await ai_matching_service.create_itinerary_from_sites(
                                    matched_cities,
                                    travel_id,
                                    user_id
                                )
                                logger.info(f"Itinerario creado exitosamente para travel_id={travel_id} con {len(matched_cities)} sitios")
                            else:
                                logger.warning("No se encontraron sitios válidos para crear el itinerario")

                        except Exception as e:
                            logger.error(f"Error creando itinerario: {str(e)}", exc_info=True)

            except Exception as e:
                logger.error(f"Error en el asistente: {str(e)}", exc_info=True)
                assistant_response = "Lo siento, hubo un error al procesar tu mensaje."

            # Guardar respuesta del asistente
            assistant_message = MessageCreate(
                content=assistant_response,
                is_user=False,
                travel_id=travel_id
            )
            saved_assistant_message = await self.create_message(db, travel_id, "assistant", assistant_message)
            logger.info(f"Respuesta del asistente guardada: {saved_assistant_message.id}")

            # Devolver ambos mensajes
            current_time = datetime.utcnow()
            response_data = {
                "type": "message",
                "data": {
                    "content": assistant_response,
                    "is_user": False,
                    "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "user_id": "assistant",
                    "id": str(saved_assistant_message.id),
                    "travel_id": travel_id
                }
            }
            logger.info(f"Enviando respuesta: {response_data}")
            return response_data

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_chat_messages(
        self,
        travel_id: str,
        user_id: str,
        db: AsyncIOMotorDatabase,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """
        Obtiene los mensajes de un viaje específico.
        """
        try:
            # Verificar que el viaje existe y pertenece al usuario
            travel = await travel_crud.get_travel(db, travel_id)
            if not travel or str(travel.user_id) != user_id:
                raise HTTPException(status_code=404, detail="Travel not found or unauthorized")

            # Obtener mensajes
            messages = await get_messages_collection()
            cursor = messages.find({
                "travel_id": travel_id
            }).sort("timestamp", -1).skip(skip).limit(limit)

            message_list = [Message(**doc) async for doc in cursor]
            message_list.reverse()  # Invertir para orden cronológico
            return message_list

        except Exception as e:
            logger.error(f"Error getting chat messages: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_message(
        self,
        db: AsyncIOMotorDatabase,
        travel_id: str,
        user_id: str,
        message: MessageCreate
    ) -> Message:
        """
        Crea un nuevo mensaje para un viaje.
        """
        try:
            logger.info(f"Creating message for travel_id={travel_id}, user_id={user_id}")

            # Crear el mensaje
            messages = await get_messages_collection()
            message_dict = message.dict()
            message_dict["user_id"] = user_id
            message_dict["created_at"] = datetime.utcnow()
            message_dict["updated_at"] = datetime.utcnow()
            message_dict["timestamp"] = datetime.utcnow()
            message_dict["travel_id"] = travel_id

            result = await messages.insert_one(message_dict)
            created_message = await messages.find_one({"_id": result.inserted_id})
            
            if not created_message:
                raise HTTPException(status_code=500, detail="Failed to create message")
            
            # Convertir el ObjectId a string para la respuesta
            created_message["_id"] = str(created_message["_id"])
            
            logger.info(f"Message created successfully: id={created_message['_id']}, travel_id={travel_id}")
            return Message(**created_message)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

# Crear una instancia global del servicio de chat
chat_service = ChatService() 