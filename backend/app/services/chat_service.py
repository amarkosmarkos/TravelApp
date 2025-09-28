"""
Servicio de chat que maneja la comunicación con el asistente de viajes.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from app.database import get_messages_collection, get_itineraries_collection
from app.models.travel import ChatMessageCreate, Message
from bson import ObjectId
from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow
from app.agents.message_router import MessageRouter, MessageType

logger = logging.getLogger(__name__)

class ChatService:
    """
    Servicio para manejar mensajes de chat y procesamiento de itinerarios.
    """
    
    def __init__(self):
        self.smart_workflow = SmartItineraryWorkflow()
        self.message_router = MessageRouter()
        # Anti-duplicados simple en memoria: (user, travel, msg_norm) -> timestamp
        self._recent_messages: Dict[str, float] = {}
        self._recent_ttl_sec = 3.0
    
    async def process_message(self, message: str, user_id: str, travel_id: str, db=None) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario usando el SmartItineraryWorkflow.
        """
        try:
            logger.info(f"Procesando mensaje: {message}")

            # Deduplicación: evitar doble procesamiento del mismo mensaje en ventana corta
            import time
            msg_norm = (message or "").strip().lower()
            dedup_key = f"{user_id}:{travel_id}:{msg_norm}"
            now = time.time()
            last_ts = self._recent_messages.get(dedup_key)
            if last_ts and (now - last_ts) < self._recent_ttl_sec:
                logger.info("Mensaje duplicado detectado, ignorando procesamiento")
                # No guardar nuevamente; devolver respuesta neutra para que WS no envíe
                return {
                    "message": "",
                    "is_user": False,
                    "intention": "duplicate_ignored",
                    "classification": {
                        "type": "duplicate",
                        "confidence": 1.0,
                        "reason": "Mensaje repetido en ventana corta",
                        "extracted_country": ""
                    },
                    "travel_id": travel_id,
                    "user_id": user_id
                }
            # Registrar mensaje
            self._recent_messages[dedup_key] = now
            
            # Guardar mensaje del usuario
            await self._save_user_message(message, user_id, travel_id)

            # Verificación temprana: si el viaje no existe (fue borrado), informar y pedir nueva configuración
            try:
                from app.database import get_travels_collection
                from bson import ObjectId
                travels = await get_travels_collection()
                tr_exists = await travels.find_one({"_id": ObjectId(travel_id)})
                if not tr_exists:
                    assistant_message = (
                        "No encuentro la configuración de este viaje (posiblemente fue borrado). "
                        "Indícame el país y la duración (por ejemplo, 14 días) para crear uno nuevo, "
                        "o vuelve a realizar la configuración inicial."
                    )
                    await self._save_assistant_message(assistant_message, user_id, travel_id)
                    return {
                        "message": assistant_message,
                        "is_user": False,
                        "intention": "clarify",
                        "classification": {
                            "type": "clarify",
                            "confidence": 1.0,
                            "reason": "travel_not_found",
                            "extracted_country": ""
                        },
                        "travel_id": travel_id,
                        "user_id": user_id
                    }
            except Exception as e:
                logger.warning(f"No se pudo verificar existencia del viaje {travel_id}: {e}")

            # Construir contexto del travel para clasificación inteligente
            travel_ctx = {}
            try:
                from app.database import get_travels_collection, get_itineraries_collection
                travels = await get_travels_collection()
                itineraries = await get_itineraries_collection()
                tr = await travels.find_one({"_id": ObjectId(travel_id)})
                it = await itineraries.find_one({"travel_id": travel_id})
                if tr:
                    travel_ctx = {
                        "travel_id": travel_id,
                        "country": tr.get("country") or tr.get("destination"),
                        "total_days": tr.get("total_days"),
                        "has_setup": bool((tr.get("country") or tr.get("destination")) and tr.get("total_days")),
                        "has_itinerary": bool(it is not None)
                    }
            except Exception as e:
                logger.warning(f"No se pudo construir travel context: {e}")

            # Clasificar intención (gating) con function calling
            classification = await self.message_router.classify_message(message, context=travel_ctx)
            message_type = classification.get("type", MessageType.GENERAL_CHAT)
            confidence = classification.get("confidence", 0.0)
            # Prefer country/total_days from classification/tools o contexto
            country = classification.get("extracted_country") or travel_ctx.get("country") or self._extract_country_from_message(message) or "thailand"
            extracted_days = classification.get("total_days")

            # Umbral para acciones automáticas
            auto_threshold = 0.75

            # Si es chat general o confianza baja, pedir aclaración y no crear nada
            # EXCEPTO si hay TravelSetup guardado y el mensaje es preferencias: disparamos CREATE_ITINERARY
            if (message_type == MessageType.GENERAL_CHAT) or (confidence < auto_threshold and message_type not in (MessageType.CREATE_ITINERARY, MessageType.MODIFY_ITINERARY)):
                try:
                    # Comprobar configuración del travel
                    from app.database import get_travels_collection
                    travels = await get_travels_collection()
                    tr = await travels.find_one({"_id": ObjectId(travel_id)})
                    if tr and (tr.get("destination") or tr.get("country")) and (tr.get("total_days")):
                        # Tratar como preferencias y crear itinerario
                        logger.info("Preferencias detectadas con TravelSetup presente. Disparando creación de itinerario.")
                        country_eff = (tr.get("country") or tr.get("destination") or country)
                        total_days = int(extracted_days or tr.get("total_days") or 7)
                        response = await self.smart_workflow.process_smart_request(
                            user_input=message,
                            user_id=user_id,
                            travel_id=travel_id,
                            country=country_eff
                        )
                        assistant_message = response.get("message", "Itinerario creado.")
                        await self._save_assistant_message(assistant_message, user_id, travel_id)
                        logger.info(f"Itinerario disparado por preferencias. country={country_eff}, total_days={total_days}")
                        return {
                            "message": assistant_message,
                            "is_user": False,
                            "intention": response.get("intention", "itinerary_created"),
                            "classification": classification,
                            "travel_id": travel_id,
                            "user_id": user_id
                        }
                except Exception as e:
                    logger.warning(f"Fallo al disparar por preferencias con TravelSetup: {e}")
                assistant_message = (
                    "¡Hola! ¿Quieres que te cree un itinerario o modificar uno existente? "
                    "Dime país y duración (por ejemplo, 14 días) y el estilo (playa, historia, naturaleza, gastronomía)."
                )
                await self._save_assistant_message(assistant_message, user_id, travel_id)
                return {
                    "message": assistant_message,
                    "is_user": False,
                    "intention": "clarify",
                    "classification": {
                        "type": message_type.value if hasattr(message_type, 'value') else str(message_type),
                        "confidence": confidence,
                        "reason": classification.get("reason", "Baja confianza o chat general"),
                        "extracted_country": country
                    },
                    "travel_id": travel_id,
                    "user_id": user_id
                }
            
            # ⭐ USAR EL NUEVO FLUJO CON SELECCIÓN ANTES DEL GRAFO
            response = await self.smart_workflow.process_smart_request(
                user_input=message,
                user_id=user_id,
                travel_id=travel_id,
                country=country
            )
            
            # Asegurar que la respuesta tenga la estructura correcta
            assistant_message = response.get("message", "Lo siento, no pude procesar tu mensaje.")
            
            # Guardar respuesta del asistente
            await self._save_assistant_message(assistant_message, user_id, travel_id)
            
            # Normalizar clasificación para ser JSON-serializable
            type_str = message_type.value if hasattr(message_type, 'value') else str(message_type)
            classification_out = {
                "type": type_str,
                "confidence": confidence,
                "reason": classification.get("reason", ""),
                "extracted_country": country
            }

            # Devolver respuesta con estructura correcta
            return {
                "message": assistant_message,
                "is_user": False,
                "intention": response.get("intention", "unknown"),
                "classification": response.get("classification", classification_out),
                "travel_id": travel_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            error_message = f"Lo siento, hubo un error procesando tu mensaje: {str(e)}"
            await self._save_assistant_message(error_message, user_id, travel_id)
            return {
                "message": error_message,
                "is_user": False,
                "intention": "error"
            }
    
    async def _save_user_message(self, message: str, user_id: str, travel_id: str):
        """Guarda un mensaje del usuario en la base de datos."""
        try:
            messages_collection = await get_messages_collection()
            message_data = ChatMessageCreate(
                content=message,
                is_user=True,
                user_id=user_id,
                travel_id=travel_id
            )
            await messages_collection.insert_one(message_data.dict())
            logger.info(f"Mensaje del usuario guardado para travel {travel_id}")
        except Exception as e:
            logger.error(f"Error guardando mensaje del usuario: {e}")
    
    async def _save_assistant_message(self, message: str, user_id: str, travel_id: str):
        """Guarda un mensaje del asistente en la base de datos."""
        try:
            messages_collection = await get_messages_collection()
            message_data = ChatMessageCreate(
                content=message,
                is_user=False,
                user_id=user_id,
                travel_id=travel_id
            )
            await messages_collection.insert_one(message_data.dict())
            logger.info(f"Mensaje del asistente guardado para travel {travel_id}")
        except Exception as e:
            logger.error(f"Error guardando mensaje del asistente: {e}")
    
    async def get_chat_messages(self, travel_id: str, user_id: str, db, skip: int = 0, limit: int = 50) -> List[Dict]:
        try:
            logger.info(f"Getting chat messages for travel {travel_id}, user {user_id}")
            messages_collection = await get_messages_collection()
            messages = await messages_collection.find(
                {"travel_id": travel_id}
            ).sort("timestamp", 1).skip(skip).limit(limit).to_list(length=None)
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": str(msg["_id"]),
                    "content": msg["content"],
                    "is_user": msg["is_user"],
                    "timestamp": msg.get("timestamp", msg.get("created_at", datetime.utcnow())).isoformat(),
                    "user_id": msg.get("user_id", "unknown"),
                    "travel_id": msg["travel_id"]
                })
            logger.info(f"Retrieved {len(formatted_messages)} messages for travel {travel_id}")
            return formatted_messages
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []
    
    async def create_message(self, message_data: ChatMessageCreate) -> Dict[str, Any]:
        """Crea un nuevo mensaje en la base de datos."""
        try:
            messages_collection = await get_messages_collection()
            result = await messages_collection.insert_one(message_data.dict())
            return {"id": str(result.inserted_id), "success": True}
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return {"success": False, "error": str(e)}

    def _extract_country_from_message(self, message: str) -> str:
        """
        Extrae el país del mensaje del usuario.
        """
        message_lower = message.lower()
        
        # Mapeo de países
        country_mapping = {
            "tailandia": "thailand",
            "thailand": "thailand",
            "tailandés": "thailand",
            "tailandesa": "thailand",
            "bangkok": "thailand",
            "chiang mai": "thailand",
            "phuket": "thailand",
            "krabi": "thailand",
            "ayutthaya": "thailand",
            "pataya": "thailand",
            "pattaya": "thailand",
            "koh samui": "thailand",
            "koh phangan": "thailand",
            "koh tao": "thailand"
        }
        
        for keyword, country_code in country_mapping.items():
            if keyword in message_lower:
                return country_code
        
        return "thailand"  # Default

# Instancia global
chat_service = ChatService() 