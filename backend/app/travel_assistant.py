from typing import List, Dict, Any
from openai import AzureOpenAI
from app.config import settings
from app.services.city_service import city_service
import json
import logging

logger = logging.getLogger(__name__)

class TravelAssistant:
    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    async def create_itinerary(self, cities: List[str], country_code: str) -> Dict[str, Any]:
        """
        Create a travel itinerary with city details from the database.
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

            # Create a detailed message about the itinerary
            message_parts = ["He creado un itinerario que incluye:"]
            for city in city_details:
                if city["population"] and city["coordinates"]:
                    message_parts.append(
                        f"- {city['name']} (Población: {city['population']:,}, "
                        f"Coordenadas: {city['coordinates']['latitude']:.4f}, "
                        f"{city['coordinates']['longitude']:.4f})"
                    )
                else:
                    message_parts.append(f"- {city['name']}")

            return {
                "intention": "reformulate_itinerary",
                "cities": city_details,
                "user_message": "\n".join(message_parts) + "\n\n¿Te gustaría que ajustemos algo?"
            }
        except Exception as e:
            logger.error(f"Error creating itinerary: {str(e)}")
            return {
                "intention": "error",
                "cities": [],
                "user_message": f"Lo siento, ha ocurrido un error al crear el itinerario: {str(e)}"
            }

    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process the user message and determine if it's a request to reformulate an itinerary.
        Uses function calling to extract cities and generate appropriate response.
        """
        # Define the function that can be called by the model
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_itinerary",
                    "description": "Create a travel itinerary with the specified cities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of cities to include in the itinerary"
                            },
                            "country_code": {
                                "type": "string",
                                "description": "ISO country code (e.g., 'ID' for Indonesia)"
                            }
                        },
                        "required": ["cities", "country_code"]
                    }
                }
            }
        ]

        # System message to guide the model's behavior
        system_message = """You are a proactive travel assistant. Your main tasks are:
1. Detect if the user wants to create or modify a travel itinerary
2. When a country or region is mentioned, automatically suggest relevant cities and create an itinerary
3. If the user mentions specific cities, use those in the itinerary
4. If the user is vague about locations, suggest popular destinations in the mentioned country/region
5. Always provide a complete list of cities - never ask the user to provide cities
6. Be knowledgeable about popular tourist destinations and create logical travel routes
7. Always include the country code in your function calls (e.g., 'ID' for Indonesia)

For example:
- If user says "I want to visit Indonesia", suggest popular cities like Bali, Jakarta, Yogyakarta, etc.
- If user says "just a fucking itinerary in indonesia", understand the frustration and provide a complete itinerary with major cities
- If user mentions specific cities, use those but also suggest complementary destinations

Remember: Never ask the user to provide cities - you should always suggest them based on the context."""

        try:
            # Call Azure OpenAI with function calling enabled
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                tools=tools,
                tool_choice="auto"
            )

            # Get the response message
            response_message = response.choices[0].message

            # Check if the model called the function
            if response_message.tool_calls:
                # Get the function call details
                tool_call = response_message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Call the appropriate function
                if function_name == "create_itinerary":
                    return await self.create_itinerary(
                        cities=function_args["cities"],
                        country_code=function_args["country_code"]
                    )

            # If no function was called, return the model's response
            return {
                "intention": "other",
                "cities": [],
                "user_message": response_message.content
            }

        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            return {
                "intention": "error",
                "cities": [],
                "user_message": f"Lo siento, ha ocurrido un error al procesar tu mensaje: {str(e)}"
            }

# Create a singleton instance
travel_assistant = TravelAssistant() 