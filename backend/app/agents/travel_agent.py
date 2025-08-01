"""
Agente principal de viajes que orquesta todo el proceso de creación de itinerarios.
"""

from typing import Dict, Any, List
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langfuse import Langfuse
import logging

from .database_agent import DatabaseAgent
from .routing_agent import RoutingAgent
from .itinerary_agent import ItineraryAgent

logger = logging.getLogger(__name__)

class TravelAgent:
    """
    Agente principal que coordina la creación de itinerarios de viaje.
    """
    
    def __init__(self, langfuse_client: Langfuse = None):
        self.langfuse = langfuse_client
        self.db_agent = DatabaseAgent()
        self.routing_agent = RoutingAgent()
        self.itinerary_agent = ItineraryAgent()
        
        # Memory para mantener contexto
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Herramientas disponibles
        self.tools = self._create_tools()
        
        # Agente principal
        self.agent = OpenAIFunctionsAgent.from_llm_and_tools(
            llm=self._get_llm(),
            tools=self.tools,
            system_message=self._get_system_prompt()
        )
        
        # Executor
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _get_llm(self):
        """Obtiene el LLM configurado."""
        from app.config import settings
        from langchain_openai import AzureChatOpenAI
        
        return AzureChatOpenAI(
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0.1
        )
    
    def _get_system_prompt(self) -> str:
        """Prompt del sistema para el agente principal."""
        return """Eres un asistente de viajes experto. Tu tarea es ayudar a los usuarios a crear itinerarios de viaje.

PROCESO DE TRABAJO:
1. Cuando un usuario menciona un país o destino, usa search_cities_in_database para encontrar ciudades disponibles
2. Analiza las ciudades encontradas y determina cuáles son más relevantes
3. Usa calculate_optimal_route para encontrar la ruta más eficiente entre las ciudades
4. Finalmente, usa create_itinerary para generar el itinerario final

INSTRUCCIONES:
- Siempre busca en la base de datos primero
- Considera la distancia y tiempo de viaje entre ciudades
- Crea itinerarios realistas y atractivos
- Responde de manera conversacional y útil
"""
    
    def _create_tools(self) -> List[BaseTool]:
        """Crea las herramientas disponibles para el agente."""
        from langchain.tools import tool
        
        @tool
        def search_cities_in_database(country_name: str) -> str:
            """Busca ciudades disponibles en la base de datos para un país específico."""
            try:
                cities = self.db_agent.search_cities_by_country(country_name)
                return f"Ciudades encontradas para {country_name}: {cities}"
            except Exception as e:
                logger.error(f"Error buscando ciudades: {e}")
                return f"Error al buscar ciudades para {country_name}: {str(e)}"
        
        @tool
        def calculate_optimal_route(cities: List[str]) -> str:
            """Calcula la ruta óptima entre las ciudades seleccionadas."""
            try:
                route = self.routing_agent.calculate_route(cities)
                return f"Ruta óptima calculada: {route}"
            except Exception as e:
                logger.error(f"Error calculando ruta: {e}")
                return f"Error al calcular ruta: {str(e)}"
        
        @tool
        def create_itinerary(country: str, cities: List[str], route: str) -> str:
            """Crea un itinerario detallado basado en el país, ciudades y ruta."""
            try:
                itinerary = self.itinerary_agent.create_itinerary(country, cities, route)
                return f"Itinerario creado: {itinerary}"
            except Exception as e:
                logger.error(f"Error creando itinerario: {e}")
                return f"Error al crear itinerario: {str(e)}"
        
        return [search_cities_in_database, calculate_optimal_route, create_itinerary]
    
    async def process_request(self, user_message: str, user_id: str) -> Dict[str, Any]:
        """
        Procesa una solicitud del usuario y genera una respuesta.
        """
        try:
            # Ejecutar agente sin observabilidad por ahora
            # TODO: Implementar observabilidad con Langfuse cuando esté disponible
            response = await self.agent_executor.ainvoke(
                {"input": user_message}
            )
            
            return {
                "message": response["output"],
                "is_user": False,
                "intention": "itinerary_created" if "itinerario" in response["output"].lower() else "conversation"
            }
            
        except Exception as e:
            logger.error(f"Error procesando solicitud: {e}")
            return {
                "message": f"Lo siento, hubo un error procesando tu solicitud: {str(e)}",
                "is_user": False,
                "intention": "error"
            } 