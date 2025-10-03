"""
Main travel agent orchestrating the itinerary creation process.
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
    Main agent that coordinates travel itinerary creation.
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
        """Get configured LLM instance."""
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
        """System prompt for the main agent (English)."""
        return """You are an expert travel assistant. Your task is to help users create travel itineraries.

WORKFLOW:
1) When the user mentions a country or destination, use search_cities_in_database to find available cities
2) Analyze the cities and determine which ones are most relevant
3) Use calculate_optimal_route to compute an efficient route
4) Finally, use create_itinerary to generate the final itinerary

INSTRUCTIONS:
- Always consult the database first when possible
- Consider distance and travel time between cities
- Create realistic and attractive itineraries
- ALWAYS respond in the user's preferred language (default: English)
"""
    
    def _create_tools(self) -> List[BaseTool]:
        """Crea las herramientas disponibles para el agente."""
        from langchain.tools import tool
        
        @tool
        def search_cities_in_database(country_name: str) -> str:
            """Search available cities in the database for a given country."""
            try:
                cities = self.db_agent.search_cities_by_country(country_name)
                return f"Cities found for {country_name}: {cities}"
            except Exception as e:
                logger.error(f"Error searching cities: {e}")
                return f"Error searching cities for {country_name}: {str(e)}"
        
        @tool
        def calculate_optimal_route(cities: List[str]) -> str:
            """Calculate the optimal route among selected cities."""
            try:
                route = self.routing_agent.calculate_route(cities)
                return f"Optimal route calculated: {route}"
            except Exception as e:
                logger.error(f"Error calculating route: {e}")
                return f"Error calculating route: {str(e)}"
        
        @tool
        def create_itinerary(country: str, cities: List[str], route: str) -> str:
            """Create a detailed itinerary based on country, cities and route."""
            try:
                itinerary = self.itinerary_agent.create_itinerary(country, cities, route)
                return f"Itinerary created: {itinerary}"
            except Exception as e:
                logger.error(f"Error creating itinerary: {e}")
                return f"Error creating itinerary: {str(e)}"
        
        return [search_cities_in_database, calculate_optimal_route, create_itinerary]
    
    async def process_request(self, user_message: str, user_id: str) -> Dict[str, Any]:
        """
        Process a user request and generate a response.
        """
        try:
            # Ejecutar agente sin observabilidad por ahora
            # TODO: Implement observability with Langfuse when available
            response = await self.agent_executor.ainvoke(
                {"input": user_message}
            )
            
            return {
                "message": response["output"],
                "is_user": False,
                "intention": "itinerary_created" if "itinerary" in response["output"].lower() else "conversation"
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "message": f"Sorry, there was an error processing your request: {str(e)}",
                "is_user": False,
                "intention": "error"
            } 