"""
Grafo de flujo de trabajo usando LangGraph para orquestar los agentes de viajes.
"""

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import BaseTool
import logging
import json

from .travel_agent import TravelAgent
from .database_agent import DatabaseAgent
from .routing_agent import RoutingAgent
from .itinerary_agent import ItineraryAgent

logger = logging.getLogger(__name__)

# Definir el estado del grafo
class AgentState(TypedDict):
    """Estado del grafo de agentes."""
    messages: List[HumanMessage | AIMessage]
    user_input: str
    country: str
    cities: List[Dict[str, Any]]
    route: Dict[str, Any]
    itinerary: Dict[str, Any]
    error: str
    step: str

class TravelWorkflowGraph:
    """
    Grafo de flujo de trabajo para el sistema de agentes de viajes.
    """
    
    def __init__(self):
        self.travel_agent = TravelAgent()
        self.db_agent = DatabaseAgent()
        self.routing_agent = RoutingAgent()
        self.itinerary_agent = ItineraryAgent()
        
        # Crear el grafo
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """
        Crea el grafo de flujo de trabajo.
        """
        # Crear el grafo
        workflow = StateGraph(AgentState)
        
        # Agregar nodos
        workflow.add_node("extract_country", self._extract_country)
        workflow.add_node("search_cities", self._search_cities)
        workflow.add_node("calculate_route", self._calculate_route)
        workflow.add_node("create_itinerary", self._create_itinerary)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Definir el flujo
        workflow.set_entry_point("extract_country")
        
        # Flujo principal
        workflow.add_edge("extract_country", "search_cities")
        workflow.add_edge("search_cities", "calculate_route")
        workflow.add_edge("calculate_route", "create_itinerary")
        workflow.add_edge("create_itinerary", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Manejo de errores
        workflow.add_edge("extract_country", "handle_error")
        workflow.add_edge("search_cities", "handle_error")
        workflow.add_edge("calculate_route", "handle_error")
        workflow.add_edge("create_itinerary", "handle_error")
        workflow.add_edge("handle_error", END)
        
        # Compilar el grafo
        return workflow.compile()
    
    async def _extract_country(self, state: AgentState) -> AgentState:
        """
        Extrae el país del mensaje del usuario.
        """
        try:
            state["step"] = "extract_country"
            
            # Usar el agente principal para extraer el país
            response = await self.travel_agent.process_request(
                state["user_input"], 
                "workflow"
            )
            
            # Extraer país del mensaje (simplificado)
            country = self._extract_country_from_message(state["user_input"])
            state["country"] = country
            
            # Agregar mensaje del sistema
            state["messages"].append(
                AIMessage(content=f"País identificado: {country}")
            )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error extrayendo país: {str(e)}"
            return state
    
    async def _search_cities(self, state: AgentState) -> AgentState:
        """
        Busca ciudades en la base de datos.
        """
        try:
            state["step"] = "search_cities"
            
            # Buscar ciudades en la base de datos
            cities = await self.db_agent.search_cities_by_country(state["country"])
            state["cities"] = cities
            
            # Agregar mensaje del sistema
            state["messages"].append(
                AIMessage(content=f"Encontradas {len(cities)} ciudades para {state['country']}")
            )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error buscando ciudades: {str(e)}"
            return state
    
    async def _calculate_route(self, state: AgentState) -> AgentState:
        """
        Calcula la ruta óptima entre las ciudades.
        """
        try:
            state["step"] = "calculate_route"
            
            if not state["cities"]:
                state["error"] = "No se encontraron ciudades para calcular la ruta"
                return state
            
            # Calcular ruta óptima
            route = self.routing_agent.calculate_route(state["cities"])
            state["route"] = route
            
            # Agregar mensaje del sistema
            state["messages"].append(
                AIMessage(content=f"Ruta calculada: {route['total_distance']:.1f} km")
            )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error calculando ruta: {str(e)}"
            return state
    
    async def _create_itinerary(self, state: AgentState) -> AgentState:
        """
        Crea el itinerario detallado.
        """
        try:
            state["step"] = "create_itinerary"
            
            if not state["route"]:
                state["error"] = "No hay ruta disponible para crear el itinerario"
                return state
            
            # Crear itinerario
            itinerary = self.itinerary_agent.create_itinerary(
                state["country"],
                state["cities"],
                state["route"]
            )
            state["itinerary"] = itinerary
            
            # Agregar mensaje del sistema
            state["messages"].append(
                AIMessage(content="Itinerario creado exitosamente")
            )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error creando itinerario: {str(e)}"
            return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """
        Genera la respuesta final para el usuario.
        """
        try:
            state["step"] = "generate_response"
            
            # Crear respuesta final
            response = self._create_final_response(state)
            
            # Agregar respuesta final
            state["messages"].append(
                AIMessage(content=response)
            )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error generando respuesta: {str(e)}"
            return state
    
    async def _handle_error(self, state: AgentState) -> AgentState:
        """
        Maneja errores en el flujo.
        """
        state["step"] = "handle_error"
        
        error_message = state.get("error", "Error desconocido en el flujo")
        
        # Agregar mensaje de error
        state["messages"].append(
            AIMessage(content=f"Lo siento, hubo un error: {error_message}")
        )
        
        return state
    
    def _extract_country_from_message(self, message: str) -> str:
        """
        Extrae el país del mensaje del usuario (simplificado).
        """
        # Mapeo de países comunes
        country_mapping = {
            "thailand": "Thailand",
            "japan": "Japan",
            "spain": "Spain",
            "france": "France",
            "italy": "Italy",
            "germany": "Germany",
            "uk": "United Kingdom",
            "england": "United Kingdom",
            "usa": "United States",
            "america": "United States",
            "china": "China",
            "korea": "South Korea",
            "australia": "Australia",
            "canada": "Canada",
            "brazil": "Brazil",
            "argentina": "Argentina",
            "mexico": "Mexico",
            "peru": "Peru",
            "chile": "Chile",
            "colombia": "Colombia"
        }
        
        message_lower = message.lower()
        
        for country_key, country_name in country_mapping.items():
            if country_key in message_lower:
                return country_name
        
        # Si no se encuentra, devolver el primer país mencionado
        return "Thailand"  # Fallback
    
    def _create_final_response(self, state: AgentState) -> str:
        """
        Crea la respuesta final para el usuario.
        """
        try:
            itinerary = state.get("itinerary", {})
            
            if "error" in itinerary:
                return f"Lo siento, no pude crear el itinerario: {itinerary['error']}"
            
            # Extraer el itinerario generado
            itinerary_text = itinerary.get("itinerary", "No se pudo generar el itinerario")
            
            # Crear resumen
            summary = itinerary.get("summary", {})
            country = summary.get("country", "Desconocido")
            total_cities = summary.get("total_cities", 0)
            total_distance = summary.get("total_distance_km", 0)
            
            response = f"""
¡Perfecto! He creado un itinerario detallado para tu viaje a {country}.

📋 RESUMEN DEL VIAJE:
• País: {country}
• Ciudades a visitar: {total_cities}
• Distancia total: {total_distance:.1f} km

🗺️ ITINERARIO DETALLADO:
{itinerary_text}

¡Espero que disfrutes tu viaje! Si necesitas más detalles o quieres modificar algo, no dudes en preguntarme.
"""
            
            return response.strip()
            
        except Exception as e:
            return f"Error generando respuesta final: {str(e)}"
    
    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Procesa una solicitud del usuario usando el flujo de trabajo.
        """
        try:
            # Crear estado inicial
            initial_state = AgentState(
                messages=[HumanMessage(content=user_input)],
                user_input=user_input,
                country="",
                cities=[],
                route={},
                itinerary={},
                error="",
                step=""
            )
            
            # Ejecutar el flujo
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Extraer respuesta final
            final_message = final_state["messages"][-1].content
            
            return {
                "message": final_message,
                "is_user": False,
                "intention": "itinerary_created" if "itinerario" in final_message.lower() else "conversation",
                "workflow_state": {
                    "step": final_state.get("step", ""),
                    "country": final_state.get("country", ""),
                    "cities_count": len(final_state.get("cities", [])),
                    "has_route": bool(final_state.get("route")),
                    "has_itinerary": bool(final_state.get("itinerary")),
                    "error": final_state.get("error", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error en el flujo de trabajo: {e}")
            return {
                "message": f"Lo siento, hubo un error procesando tu solicitud: {str(e)}",
                "is_user": False,
                "intention": "error"
            } 