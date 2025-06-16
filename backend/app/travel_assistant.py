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
    get_chat_messages_collection,
    get_messages_collection
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
        self.system_message = """Eres un asistente de viajes de Voasis. Tu tarea es ayudar a los usuarios a planificar sus viajes.

INSTRUCCIONES:
1. Si el usuario menciona una ubicación (país, región o ciudad), usa la función create_itinerary.
2. Para otros mensajes, responde de manera amigable y útil.
3. Si el usuario saluda o hace preguntas generales, responde de forma natural.

FORMATO:
- Usa viñetas cuando proporciones información estructurada
- Mantén las respuestas claras y concisas
- Sé amigable y profesional
"""
        # Definir las funciones disponibles
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_itinerary",
                    "description": "Crea un itinerario de viaje para las ciudades especificadas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de ciudades para el itinerario"
                            },
                            "country_code": {
                                "type": "string",
                                "description": "Código de país ISO (ej: ES, FR, IT)"
                            }
                        },
                        "required": ["cities", "country_code"]
                    }
                }
            }
        ]

    async def process_message(self, message: str, user_id: str) -> dict:
        try:
            logger.info(f"Procesando mensaje del usuario {user_id}: {message}")
            
            # Obtener el historial de mensajes
            messages_collection = await get_messages_collection()
            messages = await messages_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(10).to_list(length=None)
            
            logger.info(f"Historial de mensajes obtenido: {len(messages)} mensajes")
            
            # Preparar el historial de conversación
            conversation_history = [
                {"role": "system", "content": self.system_message}
            ]
            
            for msg in reversed(messages):
                conversation_history.append({
                    "role": "user" if msg["is_user"] else "assistant",
                    "content": msg["content"]
                })
            
            # Agregar el mensaje actual
            conversation_history.append({
                "role": "user",
                "content": message
            })
            
            logger.info("Enviando mensaje a Azure OpenAI")
            
            # Llamar al modelo con function calling
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=conversation_history,
                functions=[self.tools[0]["function"]],
                function_call="auto"
            )

            # Procesar la respuesta
            response_message = response.choices[0].message
            logger.info(f"Respuesta recibida de Azure OpenAI: {response_message}")
            
            if response_message.function_call:
                # Si el modelo quiere llamar a una función
                function_name = response_message.function_call.name
                function_args = json.loads(response_message.function_call.arguments)
                logger.info(f"Llamando a función {function_name} con args: {function_args}")
                
                if function_name == "create_itinerary":
                    # Crear el itinerario
                    await self.create_itinerary(**function_args)
                    return {
                        "message": "He creado un itinerario detallado para tu viaje. Puedes verlo en la sección de itinerarios.",
                        "is_user": False
                    }
            
            # Si no hay function call, devolver la respuesta normal
            if not response_message.content:
                logger.error("Respuesta vacía de Azure OpenAI")
                return {
                    "message": "Lo siento, no pude generar una respuesta adecuada. Por favor, intenta reformular tu mensaje.",
                    "is_user": False
                }
                
            return {
                "message": response_message.content,
                "is_user": False
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "message": "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, intenta de nuevo.",
                "is_user": False
            }

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
            logger.error(f"Error creating itinerary: {str(e)}", exc_info=True)
            return {
                "intention": "error",
                "cities": [],
                "user_message": f"Lo siento, ha ocurrido un error al crear el itinerario: {str(e)}"
            }

# Crear una instancia global del asistente
travel_assistant = TravelAssistant() 