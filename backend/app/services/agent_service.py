"""
Servicio que integra el sistema de agentes con la aplicación principal.
"""

from typing import Dict, Any, List
from langfuse import Langfuse
import logging
import os

from app.agents.workflow_graph import TravelWorkflowGraph
from app.agents.travel_agent import TravelAgent

logger = logging.getLogger(__name__)

class AgentService:
    """
    Servicio que integra el sistema de agentes con la aplicación existente.
    """
    
    def __init__(self):
        # Inicializar Langfuse para observabilidad
        self.langfuse = self._initialize_langfuse()
        
        # Inicializar agentes
        self.workflow_graph = TravelWorkflowGraph()
        self.travel_agent = TravelAgent(langfuse_client=self.langfuse)
        
        logger.info("AgentService inicializado correctamente")
    
    def _initialize_langfuse(self) -> Langfuse:
        """
        Inicializa Langfuse para observabilidad.
        """
        try:
            # Obtener credenciales de Langfuse desde variables de entorno
            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            
            if langfuse_public_key and langfuse_secret_key:
                return Langfuse(
                    public_key=langfuse_public_key,
                    secret_key=langfuse_secret_key,
                    host=langfuse_host
                )
            else:
                logger.warning("Langfuse no configurado. Continuando sin observabilidad.")
                return None
                
        except Exception as e:
            logger.warning(f"No se pudo inicializar Langfuse: {e}")
            return None
    
    async def process_message_with_agents(self, message: str, user_id: str, 
                                        use_workflow: bool = True) -> Dict[str, Any]:
        """
        Procesa un mensaje usando el sistema de agentes.
        
        Args:
            message: Mensaje del usuario
            user_id: ID del usuario
            use_workflow: Si usar el grafo de flujo de trabajo o el agente simple
        """
        try:
            logger.info(f"Procesando mensaje con agentes para usuario {user_id}")
            
            if use_workflow:
                # Usar el grafo de flujo de trabajo
                response = await self.workflow_graph.process_request(message)
            else:
                # Usar el agente simple
                response = await self.travel_agent.process_request(message, user_id)
            
            # Agregar información de tracking
            response["agent_system"] = "langchain_langgraph"
            response["workflow_used"] = use_workflow
            
            logger.info(f"Respuesta generada por agentes: {response.get('intention', 'unknown')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje con agentes: {e}")
            return {
                "message": f"Lo siento, hubo un error procesando tu solicitud: {str(e)}",
                "is_user": False,
                "intention": "error",
                "agent_system": "langchain_langgraph",
                "error": str(e)
            }
    
    async def create_itinerary_with_agents(self, country: str, cities: List[str] = None,
                                         preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crea un itinerario usando el sistema de agentes.
        """
        try:
            logger.info(f"Creando itinerario con agentes para {country}")
            
            # Construir mensaje para el agente
            message = f"Quiero crear un itinerario para {country}"
            if cities:
                message += f" visitando {', '.join(cities)}"
            if preferences:
                message += f" con preferencias: {preferences}"
            
            # Procesar con agentes
            response = await self.process_message_with_agents(message, "itinerary_creation")
            
            # Agregar información adicional
            response["country"] = country
            response["cities_requested"] = cities
            response["preferences"] = preferences
            
            return response
            
        except Exception as e:
            logger.error(f"Error creando itinerario con agentes: {e}")
            return {
                "message": f"Error creando itinerario: {str(e)}",
                "is_user": False,
                "intention": "error",
                "country": country,
                "error": str(e)
            }
    
    async def optimize_route_with_agents(self, cities: List[Dict[str, Any]], 
                                       optimization_type: str = "tsp") -> Dict[str, Any]:
        """
        Optimiza una ruta usando el agente de routing.
        """
        try:
            from app.agents.routing_agent import RoutingAgent
            
            routing_agent = RoutingAgent()
            
            if optimization_type == "tsp":
                route = routing_agent.calculate_route(cities)
            elif optimization_type == "time":
                route = routing_agent.optimize_for_time(cities)
            else:
                route = routing_agent.calculate_route(cities)
            
            return {
                "route": route,
                "optimization_type": optimization_type,
                "cities_count": len(cities),
                "total_distance": route.get("total_distance", 0),
                "estimated_time": route.get("estimated_time", 0)
            }
            
        except Exception as e:
            logger.error(f"Error optimizando ruta: {e}")
            return {
                "error": str(e),
                "route": None,
                "optimization_type": optimization_type
            }
    
    async def search_cities_with_agents(self, country: str) -> Dict[str, Any]:
        """
        Busca ciudades usando el agente de base de datos.
        """
        try:
            from app.agents.database_agent import DatabaseAgent
            
            db_agent = DatabaseAgent()
            cities = await db_agent.search_cities_by_country(country)
            
            return {
                "cities": cities,
                "country": country,
                "cities_count": len(cities),
                "search_successful": True
            }
            
        except Exception as e:
            logger.error(f"Error buscando ciudades: {e}")
            return {
                "cities": [],
                "country": country,
                "cities_count": 0,
                "search_successful": False,
                "error": str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de los agentes.
        """
        return {
            "langfuse_configured": self.langfuse is not None,
            "workflow_graph_ready": hasattr(self, 'workflow_graph'),
            "travel_agent_ready": hasattr(self, 'travel_agent'),
            "agent_system": "langchain_langgraph"
        }
    
    async def test_agent_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión de los agentes.
        """
        try:
            # Probar búsqueda de ciudades
            cities_result = await self.search_cities_with_agents("Thailand")
            
            # Probar optimización de ruta
            if cities_result.get("cities"):
                route_result = await self.optimize_route_with_agents(cities_result["cities"][:3])
            else:
                route_result = {"error": "No cities to test"}
            
            return {
                "database_agent": cities_result.get("search_successful", False),
                "routing_agent": "error" not in route_result,
                "langfuse": self.langfuse is not None,
                "overall_status": "healthy" if cities_result.get("search_successful") else "partial"
            }
            
        except Exception as e:
            logger.error(f"Error en test de conexión: {e}")
            return {
                "database_agent": False,
                "routing_agent": False,
                "langfuse": self.langfuse is not None,
                "overall_status": "error",
                "error": str(e)
            }

# Instancia global del servicio de agentes
agent_service = AgentService() 