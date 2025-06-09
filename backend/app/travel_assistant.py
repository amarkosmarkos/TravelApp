from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from app.config import settings
from app.services.city_service import city_service
from app.models.conversation import Conversation, Message
from app.database import (
    get_travels_collection,
    get_itineraries_collection,
    get_itinerary_items_collection,
    get_visits_collection,
    get_places_collection,
    get_flights_collection,
    get_conversations_collection,
    get_chat_messages_collection
)
from app.models.travel import Travel, ChatMessage, ChatMessageCreate
from bson import ObjectId
import json
import logging
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear un handler para archivo
log_filename = f"travel_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)

# Crear un handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Crear un formateador
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Añadir los handlers al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class TravelAssistant:
    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.system_message = """Eres un asistente de viajes de Voasis. Tu ÚNICA tarea es ayudar a los usuarios a planificar sus viajes creando itinerarios detallados.

INSTRUCCIONES CRÍTICAS:
1. CADA vez que un usuario mencione CUALQUIER ubicación (país, región o ciudad), DEBES llamar a la función create_itinerary.
2. NUNCA respondas con un mensaje normal si se menciona una ubicación.
3. SIEMPRE usa la función create_itinerary con estas reglas:

   - Siempre usa el código de país correcto (ES, FR, IT, etc.)

FORMATO:
- Usa viñetas para las ciudades
- Incluye información básica sobre cada ciudad
- Mantén las respuestas estructuradas y claras
"""

    async def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history from database"""
        try:
            conversations = await get_conversations_collection()
            conversation = await conversations.find_one({"user_id": user_id})
            if conversation:
                return [{"role": msg["role"], "content": msg["content"]} for msg in conversation["messages"]]
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    async def _save_conversation(self, user_id: str, messages: List[Dict[str, str]]):
        """Save conversation to database"""
        try:
            conversations = await get_conversations_collection()
            conversation = await conversations.find_one({"user_id": user_id})
            if not conversation:
                conversation = {
                    "user_id": user_id,
                    "messages": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await conversations.insert_one(conversation)
            
            # Update messages and timestamp
            await conversations.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "messages": messages,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")

    async def create_itinerary(self, cities: List[str], country_code: str) -> Dict[str, Any]:
        """
        Create a travel itinerary with city details from the database and generate a natural language response.
        """
        try:
            # Get city details from database
            city_details = []
            for city_name in cities:
                city = await city_service.get_city_by_name(city_name, country_code)
                if city:
                    city_details.append({
                        "name": city.name,
                        "population": city.population,
                        "coordinates": {
                            "latitude": city.latitude,
                            "longitude": city.longitude
                        }
                    })
                else:
                    # If city not found in DB, add it with basic info
                    city_details.append({
                        "name": city_name,
                        "population": None,
                        "coordinates": None
                    })

            # Create a prompt for ChatGPT to generate a natural response
            prompt = f"""Basándote en la siguiente información de ciudades, genera un mensaje natural y atractivo 
            que describa un itinerario de viaje. Incluye detalles interesantes sobre cada ciudad y sugiere 
            una experiencia de viaje coherente. Las ciudades son:

            {json.dumps(city_details, indent=2, ensure_ascii=False)}

            Genera una respuesta que sea conversacional y atractiva, como si estuvieras 
            contándole a un amigo sobre este viaje."""

            # Generate response using ChatGPT
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un experto en viajes que crea itinerarios atractivos y personalizados."},
                    {"role": "user", "content": prompt}
                ]
            )

            generated_message = response.choices[0].message.content

            return {
                "intention": "reformulate_itinerary",
                "cities": city_details,
                "user_message": generated_message + "\n\n¿Te gustaría que ajustemos algo del itinerario?"
            }
        except Exception as e:
            logger.error(f"Error creating itinerary: {str(e)}")
            return {
                "intention": "error",
                "cities": [],
                "user_message": f"Lo siento, ha ocurrido un error al crear el itinerario: {str(e)}"
            }

    async def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
        try:
            logger.info(f"Procesando mensaje para usuario {user_id}")
            
            # Obtener el historial de conversación
            chat_messages = await get_chat_messages_collection()
            messages = await chat_messages.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(10).to_list(length=10)
            
            # Procesar el mensaje y generar respuesta
            response = {
                "intention": "travel_planning",
                "cities": [],
                "user_message": message
            }
            
            # Guardar el mensaje en la base de datos
            await self.save_chat_message(user_id, message, True)
            await self.save_chat_message(user_id, str(response), False)
            
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            raise

    async def get_travel_history(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            travels = await get_travels_collection()
            return await travels.find({"user_id": user_id}).to_list(length=100)
        except Exception as e:
            logger.error(f"Error obteniendo historial: {str(e)}")
            raise

    async def save_chat_message(self, user_id: str, content: str, is_user: bool):
        try:
            chat_messages = await get_chat_messages_collection()
            message = {
                "user_id": user_id,
                "content": content,
                "is_user": is_user,
                "timestamp": datetime.utcnow()
            }
            await chat_messages.insert_one(message)
        except Exception as e:
            logger.error(f"Error guardando mensaje: {str(e)}")
            raise

# Crear una instancia global del asistente
travel_assistant = TravelAssistant() 