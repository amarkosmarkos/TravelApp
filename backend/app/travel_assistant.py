from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from app.config import settings
from app.config import ASSISTANT_PERSONALITY, load_tools
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
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear un handler para archivo
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_filename = log_dir / f"travel_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
        
        # Cargar herramientas y personalidad
        self.tools = load_tools()
        self.personality = ASSISTANT_PERSONALITY

    def _load_tools(self) -> List[Dict]:
        """Carga las herramientas desde el archivo JSON de configuración."""
        try:
            tools_path = Path(__file__).parent / "config" / "tools.json"
            with open(tools_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("tools", [])
        except Exception as e:
            logger.error(f"Error loading tools configuration: {str(e)}")
            return []

    async def process_message(self, message: str, user_id: str, message_history: List[Dict] = None) -> dict:
        try:
            logger.info(f"Procesando mensaje del usuario {user_id}: {message}")
            
            # Preparar el historial de conversación
            conversation_history = [
                {"role": "system", "content": self.personality["system_prompt"]}
            ]
            
            # Si no se proporciona historial, obtenerlo de la base de datos
            if message_history is None:
                messages_collection = await get_messages_collection()
                messages = await messages_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", 1).limit(20).to_list(length=None)
                
                logger.info(f"Historial de mensajes obtenido de la base de datos: {len(messages)} mensajes")
                
                # Añadir el historial en orden cronológico
                for msg in messages:
                    conversation_history.append({
                        "role": "user" if msg["is_user"] else "assistant",
                        "content": msg["content"]
                    })
            else:
                # Usar el historial proporcionado
                logger.info(f"Usando historial proporcionado: {len(message_history)} mensajes")
                for msg in message_history:
                    conversation_history.append({
                        "role": "user" if msg["is_user"] else "assistant",
                        "content": msg["content"]
                    })
            
            # Añadir el mensaje actual
            conversation_history.append({
                "role": "user",
                "content": message
            })
            
            logger.info("Enviando mensaje a Azure OpenAI")
            logger.debug(f"Historial de conversación: {json.dumps(conversation_history, indent=2)}")
            
            # Llamar al modelo con function calling
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=conversation_history,
                functions=[tool["function"] for tool in self.tools],
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
                    # Crear el itinerario y obtener la respuesta generada
                    itinerary_response = await self.create_itinerary(**function_args)
                    return {
                        "message": itinerary_response["user_message"],
                        "is_user": False,
                        "intention": "reformulate_itinerary",
                        "cities": itinerary_response["cities"]
                    }
            
            # Si no hay function call, devolver la respuesta normal
            if not response_message.content:
                logger.error("Respuesta vacía de Azure OpenAI")
                return {
                    "message": "No he podido generar una respuesta adecuada. ¿Podrías reformular tu mensaje?",
                    "is_user": False
                }
                
            return {
                "message": response_message.content,
                "is_user": False
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "message": f"Lo siento, ha ocurrido un error al procesar tu mensaje: {str(e)}",
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
            contándole a un amigo sobre este viaje. Incluye sugerencias de actividades, 
            lugares para visitar y consejos prácticos. Sé específico y detallado, pero 
            mantén un tono amigable y entusiasta."""

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
                "user_message": generated_message
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