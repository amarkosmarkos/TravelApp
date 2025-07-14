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
    get_messages_collection,
    get_cities_collection,
    get_sites_collection
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
            logger.info(f"Processing message from user {user_id}: {message}")
            
            # Prepare conversation history
            conversation_history = [
                {"role": "system", "content": self.personality["system_prompt"]}
            ]
            
            # If no history provided, get it from database
            if message_history is None:
                messages_collection = await get_messages_collection()
                messages = await messages_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", 1).limit(20).to_list(length=None)
                
                logger.info(f"Message history obtained from database: {len(messages)} messages")
                
                # Add history in chronological order
                for msg in messages:
                    conversation_history.append({
                        "role": "user" if msg["is_user"] else "assistant",
                        "content": msg["content"]
                    })
            else:
                # Use provided history
                logger.info(f"Using provided history: {len(message_history)} messages")
                for msg in message_history:
                    conversation_history.append({
                        "role": "user" if msg["is_user"] else "assistant",
                        "content": msg["content"]
                    })
            
            # Add current message
            conversation_history.append({
                "role": "user",
                "content": message
            })
            
            logger.info("Sending message to Azure OpenAI")
            logger.debug(f"Conversation history: {json.dumps(conversation_history, indent=2)}")
            
            # Call model with function calling
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=conversation_history,
                functions=[tool["function"] for tool in self.tools],
                function_call="auto"
            )

            # Process response
            response_message = response.choices[0].message
            logger.info(f"Response received from Azure OpenAI: {response_message}")
            
            if response_message.function_call:
                function_name = response_message.function_call.name
                function_args = json.loads(response_message.function_call.arguments)
                logger.info(f"Calling function {function_name} with args: {function_args}")
                
                # Only allow create_itinerary to be called from the outside
                if function_name == "create_itinerary":
                    itinerary_response = await self.create_itinerary(**function_args)
                    return {
                        "message": itinerary_response["user_message"],
                        "is_user": False,
                        "intention": "itinerary_created",
                        "cities": itinerary_response["cities"]
                    }
                else:
                    # If the AI tries to call determine_country_code directly, ignore and return a generic error
                    logger.warning(f"AI tried to call unsupported function: {function_name}")
                    return {
                        "message": "Sorry, I couldn't process your request. Please try again.",
                        "is_user": False
                    }
            
            # If no function call, return normal response
            if not response_message.content:
                logger.error("Empty response from Azure OpenAI")
                return {
                    "message": "I couldn't generate an appropriate response. Could you rephrase your message?",
                    "is_user": False
                }
                
            return {
                "message": response_message.content,
                "is_user": False
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "message": f"Sorry, an error occurred while processing your message: {str(e)}",
                "is_user": False
            }

    async def create_itinerary(self, cities: List[str] = None, country_code: str = None, country_name: str = None) -> Dict[str, Any]:
        """
        Create a travel itinerary by retrieving all sites from database and using AI to generate response.
        """
        try:
            logger.info(f"Creating itinerary for country: {country_name}")
            
            # STEP 1: RETRIEVE ALL SITES FROM DATABASE (names and IDs only)
            from app.database import get_sites_collection
            sites_collection = await get_sites_collection()
            
            # Get all sites with only name and ID
            all_sites = await sites_collection.find(
                {},
                {
                    "name": 1, 
                    "_id": 1
                }
            ).to_list(length=None)
            
            # Format as deterministic dictionary
            sites_dict = {}
            for site in all_sites:
                sites_dict[str(site["_id"])] = site["name"]
            
            logger.info(f"Retrieved {len(sites_dict)} sites from database")
            
            # STEP 2: DETERMINE COUNTRY CODE IF NEEDED
            if country_code is None and country_name is not None:
                country_code = await self.determine_country_code(country_name)
                logger.info(f"Determined country code: {country_code}")
            
            # STEP 3: PASS TO AI TO GENERATE ITINERARY
            prompt = f"""
            You are a travel expert. Create a travel itinerary for {country_name} (country code: {country_code}).

            AVAILABLE SITES IN DATABASE (ID: Name):
            {json.dumps(sites_dict, indent=2)}

            TASK:
            1. Generate a natural, attractive message describing a travel itinerary for {country_name}
            2. Select relevant cities/sites from the database for this country
            3. Return a JSON response with:
               - "user_message": The natural language response for the user
               - "selected_cities": List of dictionaries with "id" and "name" of selected sites

            IMPORTANT:
            - Only select sites that are relevant for {country_name}
            - Make the message conversational and attractive
            - Include activity suggestions and practical tips
            - Respond in the user's language
            """

            # Call AI to generate itinerary
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a travel expert. Return only valid JSON with user_message and selected_cities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            # Parse AI response
            ai_response = response.choices[0].message.content
            logger.info(f"AI response: {ai_response}")
            
            # Try to parse JSON response
            try:
                parsed_response = json.loads(ai_response)
                user_message = parsed_response.get("user_message", "I've created a travel itinerary for you.")
                selected_cities = parsed_response.get("selected_cities", [])
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                user_message = ai_response
                selected_cities = []

            return {
                "intention": "itinerary_created",
                "cities": selected_cities,
                "user_message": user_message,
                "sites_available": len(sites_dict)
            }
            
        except Exception as e:
            logger.error(f"Error creating itinerary: {str(e)}", exc_info=True)
            return {
                "intention": "error",
                "cities": [],
                "user_message": f"Sorry, an error occurred while creating the itinerary: {str(e)}"
            }

    async def determine_country_code(self, country_name: str) -> str:
        """
        Determines the ISO country code from the country name
        """
        try:
            # Country to ISO code mapping
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
            
            # Normalize country name
            normalized_country = country_name.lower().strip()
            
            # Search in mapping
            if normalized_country in country_mapping:
                return country_mapping[normalized_country]
            
            # If not in mapping, use AI to determine
            prompt = f"""
            I need you to determine the ISO country code for: {country_name}
            
            Respond ONLY with the 2-letter ISO country code (e.g., TH, JP, ES, FR).
            Do not include explanations or additional text.
            """
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert in ISO country codes. Respond ONLY with the 2-letter code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            country_code = response.choices[0].message.content.strip().upper()
            logger.info(f"Determined country code for {country_name}: {country_code}")
            
            return country_code
            
        except Exception as e:
            logger.error(f"Error determining country code: {str(e)}")
            # Fallback to common codes
            if "thailand" in country_name.lower():
                return "TH"
            elif "japan" in country_name.lower():
                return "JP"
            elif "spain" in country_name.lower():
                return "ES"
            else:
                return "US"  # Generic fallback

    def _get_suggested_cities_for_country(self, country_code: str) -> List[str]:
        """
        Returns suggested cities for a given country code.
        """
        city_suggestions = {
            "TH": ["Bangkok", "Chiang Mai", "Phuket", "Krabi", "Ayutthaya"],
            "JP": ["Tokyo", "Kyoto", "Osaka", "Hiroshima", "Nara"],
            "ES": ["Madrid", "Barcelona", "Seville", "Valencia", "Granada"],
            "FR": ["Paris", "Lyon", "Marseille", "Nice", "Bordeaux"],
            "IT": ["Rome", "Milan", "Florence", "Venice", "Naples"],
            "DE": ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt"],
            "GB": ["London", "Edinburgh", "Manchester", "Liverpool", "Bath"],
            "US": ["New York", "Los Angeles", "Chicago", "San Francisco", "Miami"],
            "CN": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Xi'an"],
            "KR": ["Seoul", "Busan", "Incheon", "Daegu", "Gwangju"],
            "AU": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
            "CA": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
            "BR": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Recife"],
            "AR": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Bariloche"],
            "MX": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Cancún"],
            "PE": ["Lima", "Cusco", "Arequipa", "Trujillo", "Iquitos"],
            "CL": ["Santiago", "Valparaíso", "Concepción", "La Serena", "Antofagasta"],
            "CO": ["Bogotá", "Medellín", "Cali", "Cartagena", "Barranquilla"],
            "VE": ["Caracas", "Maracaibo", "Valencia", "Barquisimeto", "Maracay"],
            "EC": ["Quito", "Guayaquil", "Cuenca", "Manta", "Ambato"],
            "BO": ["La Paz", "Santa Cruz", "Cochabamba", "Sucre", "Oruro"],
            "PY": ["Asunción", "Ciudad del Este", "San Lorenzo", "Luque", "Capiatá"],
            "UY": ["Montevideo", "Salto", "Paysandú", "Las Piedras", "Rivera"],
            "GY": ["Georgetown", "Linden", "New Amsterdam", "Corriverton", "Rose Hall"],
            "SR": ["Paramaribo", "Lelydorp", "Brokopondo", "Nieuw Nickerie", "Moengo"],
            "GF": ["Cayenne", "Matoury", "Remire-Montjoly", "Kourou", "Macouria"]
        }
        
        return city_suggestions.get(country_code, ["Capital City", "Major City 1", "Major City 2"])

# Crear una instancia global del asistente
travel_assistant = TravelAssistant() 