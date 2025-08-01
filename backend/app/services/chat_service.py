"""
Servicio de chat que maneja la comunicación con el asistente de viajes.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from app.database import get_messages_collection, get_itineraries_collection
from app.models.travel import ChatMessageCreate, Message
from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow

logger = logging.getLogger(__name__)

class ChatService:
    """
    Servicio para manejar mensajes de chat y procesamiento de itinerarios.
    """
    
    def __init__(self):
        self.smart_workflow = SmartItineraryWorkflow()
    
    async def process_message(self, message: str, user_id: str, travel_id: str, db=None) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario usando el SmartItineraryWorkflow.
        """
        try:
            logger.info(f"Procesando mensaje: {message}")
            
            # Guardar mensaje del usuario
            await self._save_user_message(message, user_id, travel_id)
            
            # Extraer país del mensaje
            country = self._extract_country_from_message(message)
            if not country:
                country = "thailand"  # Default
            
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
            
            # Devolver respuesta con estructura correcta
            return {
                "message": assistant_message,
                "is_user": False,
                "intention": response.get("intention", "unknown"),
                "classification": response.get("classification", {}),
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