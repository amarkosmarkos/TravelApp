"""
Complete intelligent itinerary management workflow using LangGraph.
"""

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import logging
import json
from datetime import datetime, timedelta

from .itinerary_detection_agent import ItineraryDetectionAgent
from .itinerary_modification_agent import ItineraryModificationAgent
from .database_agent import DatabaseAgent
from .routing_agent import RoutingAgent
from .itinerary_agent import ItineraryAgent
from .destination_selection_agent import destination_selection_agent
from app.database import get_itineraries_collection, get_travels_collection
from bson import ObjectId
from app.core.scheduler import TimeBudgetScheduler, TravelPlan
from app.core.prompt_builder import PromptBuilder
from app.services.daily_visits_service import daily_visits_service
from app.services.hotel_suggestions_service import hotel_suggestions_service
import asyncio

logger = logging.getLogger(__name__)

# Smart workflow state
class SmartItineraryState(TypedDict):
    """State of the intelligent itinerary management workflow."""
    messages: Annotated[List[HumanMessage | AIMessage], "add"]
    user_input: str
    user_id: str
    travel_id: str
    country: str
    existing_itinerary: Dict[str, Any]
    analysis: Dict[str, Any]
    available_sites: Dict[str, Any]
    modifications: Dict[str, Any]
    final_itinerary: Dict[str, Any]
    error: str
    step: str

class SmartItineraryWorkflow:
    """
    Complete intelligent itinerary management workflow.
    """
    
    def __init__(self):
        self.detection_agent = ItineraryDetectionAgent()
        self.modification_agent = ItineraryModificationAgent()
        self.db_agent = DatabaseAgent()
        self.routing_agent = RoutingAgent()
        self.itinerary_agent = ItineraryAgent()
        
        # Create the graph
        self.workflow = self._create_smart_workflow()
    
    def _create_smart_workflow(self) -> StateGraph:
        """
        Creates the smart workflow graph.
        """
        # Create the graph
        workflow = StateGraph(SmartItineraryState)
        
        # Add nodes
        workflow.add_node("detect_itinerary", self._detect_itinerary)
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("get_available_sites", self._get_available_sites)
        workflow.add_node("suggest_modifications", self._suggest_modifications)
        workflow.add_node("apply_modifications", self._apply_modifications)
        workflow.add_node("create_new_itinerary", self._create_new_itinerary)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define the flow
        workflow.set_entry_point("detect_itinerary")
        
        # Main flow
        workflow.add_edge("detect_itinerary", "analyze_request")
        workflow.add_edge("analyze_request", "get_available_sites")
        workflow.add_edge("get_available_sites", "suggest_modifications")
        workflow.add_edge("suggest_modifications", "apply_modifications")
        workflow.add_edge("apply_modifications", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Alternative flow for new itineraries
        workflow.add_edge("detect_itinerary", "create_new_itinerary")
        workflow.add_edge("create_new_itinerary", "generate_response")
        
        # Error handling
        workflow.add_edge("detect_itinerary", "handle_error")
        workflow.add_edge("analyze_request", "handle_error")
        workflow.add_edge("get_available_sites", "handle_error")
        workflow.add_edge("suggest_modifications", "handle_error")
        workflow.add_edge("apply_modifications", "handle_error")
        workflow.add_edge("create_new_itinerary", "handle_error")
        workflow.add_edge("handle_error", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def _detect_itinerary(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Detects if an itinerary exists for the trip.
        """
        try:
            state["step"] = "detect_itinerary"
            
            # Detect existing itinerary
            existing_itinerary = await self.detection_agent.detect_existing_itinerary(
                state["user_id"], 
                state["travel_id"]
            )
            
            state["existing_itinerary"] = existing_itinerary
            
            # Add system message
            if existing_itinerary.get("exists"):
                state["messages"].append(
                    AIMessage(content=f"Existing itinerary detected with {existing_itinerary['total_items']} cities")
                )
            else:
                state["messages"].append(
                    AIMessage(content="No existing itinerary found, creating a new one")
                )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error detecting itinerary: {str(e)}"
            return state
    
    async def _analyze_request(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Analyzes the user request.
        """
        try:
            state["step"] = "analyze_request"
            
            if state["existing_itinerary"].get("exists"):
                # Analizar petición para itinerario existente
                analysis = await self.detection_agent.analyze_user_request(
                    state["user_input"], 
                    state["existing_itinerary"]
                )
                state["analysis"] = analysis
                
                state["messages"].append(
                    AIMessage(content=f"Análisis completado: {analysis.get('analysis', {}).get('action_type', 'unknown')}")
                )
            else:
                # Para nuevos itinerarios, análisis básico
                state["analysis"] = {
                    "analysis": {"action_type": "create_new"},
                    "modification_needed": False
                }
            
            return state
            
        except Exception as e:
            state["error"] = f"Error analizando petición: {str(e)}"
            return state
    
    async def _get_available_sites(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Obtiene sitios disponibles para modificaciones.
        """
        try:
            state["step"] = "get_available_sites"
            
            if state["existing_itinerary"].get("exists"):
                # Obtener sitios disponibles para modificación
                current_cities = [
                    item.get("city_name") for item in state["existing_itinerary"].get("items", [])
                    if item.get("city_name")
                ]
                
                available_sites = await self.detection_agent.get_available_sites_for_modification(
                    state["country"], 
                    current_cities
                )
                
                state["available_sites"] = available_sites
                
                state["messages"].append(
                    AIMessage(content=f"Sitios disponibles: {available_sites.get('total_available', 0)}")
                )
            else:
                # Para nuevos itinerarios, obtener todos los sitios
                all_sites = await self.db_agent.search_cities_by_country(state["country"])
                state["available_sites"] = {
                    "available_sites": all_sites,
                    "total_available": len(all_sites)
                }
            
            return state
            
        except Exception as e:
            state["error"] = f"Error obteniendo sitios disponibles: {str(e)}"
            return state
    
    async def _suggest_modifications(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Sugiere modificaciones basadas en el análisis.
        """
        try:
            state["step"] = "suggest_modifications"
            
            if state["existing_itinerary"].get("exists"):
                # Sugerir modificaciones para itinerario existente
                suggestions = await self.detection_agent.suggest_modifications(
                    state["analysis"].get("analysis", {}),
                    state["available_sites"]
                )
                
                state["modifications"] = suggestions
                
                state["messages"].append(
                    AIMessage(content=f"Modificaciones sugeridas: {len(suggestions.get('cities_to_add', []))} ciudades a añadir")
                )
            else:
                # Para nuevos itinerarios, no hay modificaciones
                state["modifications"] = {}
            
            return state
            
        except Exception as e:
            state["error"] = f"Error sugiriendo modificaciones: {str(e)}"
            return state
    
    async def _apply_modifications(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Aplica las modificaciones al itinerario usando IA.
        """
        try:
            state["step"] = "apply_modifications"
            
            if state["existing_itinerary"].get("exists"):
                # Usar el NUEVO método que usa IA
                result = await self.modification_agent.apply_modifications(
                    existing_itinerary=state["existing_itinerary"]["itinerary"],
                    analysis=state["analysis"],
                    available_sites=state["available_sites"]
                )
                
                if result.get("success"):
                    state["final_itinerary"] = result
                    state["messages"].append(
                        AIMessage(content=result.get("message", "Modificaciones aplicadas exitosamente"))
                    )
                else:
                    state["error"] = result.get("error", "Error aplicando modificaciones")
            else:
                # Para nuevos itinerarios, crear desde cero
                state["final_itinerary"] = {"action": "create_new"}
            
            return state
            
        except Exception as e:
            state["error"] = f"Error aplicando modificaciones: {str(e)}"
            return state
    
    async def _create_new_itinerary(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Crea un nuevo itinerario usando IA para seleccionar destinos ANTES del grafo.
        """
        try:
            user_input = state["user_input"]
            country = state["country"]
            
            # Extraer días del mensaje del usuario
            total_days = self._extract_days_from_message(user_input)
            if not total_days:
                total_days = 7  # Default si no se especifica
            
            # ⭐ IA SELECCIONA DESTINOS ANTES DEL GRAFO
            destination_selection = await destination_selection_agent.select_destinations(
                country=country,
                total_days=total_days,
                user_preferences=None
            )
            
            # Obtener SOLO las ciudades seleccionadas por la IA
            selected_cities = destination_selection.get("selected_cities", [])
            
            if not selected_cities:
                state["error"] = "No se pudieron seleccionar destinos apropiados"
                state["step"] = "error"
                return state
            
            logger.info(f"IA seleccionó {len(selected_cities)} destinos")
            
            # ⭐ NUEVO: Usar TimeBudgetScheduler para crear plan temporal
            start_dt = datetime.utcnow()
            scheduler = TimeBudgetScheduler(total_days, start_dt)
            
            # Crear matriz de transporte
            transport_matrix = scheduler.create_transport_matrix(selected_cities)
            
            # Crear plan de viaje con tiempos reales
            travel_plan = scheduler.allocate_time(selected_cities, transport_matrix)
            
            # Asignar IDs del estado
            travel_plan.travel_id = state["travel_id"]
            travel_plan.user_id = state["user_id"]
            
            # ⭐ NUEVO: Usar PromptBuilder para generar prompt unificado
            prompt_builder = PromptBuilder()
            itinerary_prompt = prompt_builder.build_itinerary_prompt(travel_plan, country)
            
            # Generar itinerario usando el prompt unificado
            new_itinerary = self._generate_itinerary_with_unified_prompt(itinerary_prompt)
            
            # Guardar en BD con información de tiempo
            itinerary_text = new_itinerary.get("itinerary", "No se pudo generar el itinerario")
            
            # Calcular días reales del plan (exploración + transporte)
            actual_total_days = (travel_plan.total_explore_hours + travel_plan.total_travel_hours) / 24
            
            # Preparar datos del itinerario con información de tiempo
            itinerary_data = {
                "travel_id": state["travel_id"],
                "user_id": state["user_id"],
                "country": country,
                "cities": [visit.dict() for visit in travel_plan.visits],
                "route": {
                    "total_distance": 0,  # Se calculará después si es necesario
                    "estimated_time": travel_plan.total_travel_hours,
                    "algorithm": "time_budget_scheduler"
                },
                "itinerary": itinerary_text,
                "total_days": actual_total_days,  # Usar días reales calculados por el scheduler
                "exploration_days": travel_plan.total_explore_hours / 24,
                "transport_days": travel_plan.total_travel_hours / 24,
                "travel_plan": travel_plan.dict(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            save_success = await self._save_itinerary_to_database(
                user_id=state["user_id"],
                travel_id=state["travel_id"],
                country=country,
                cities=[visit.dict() for visit in travel_plan.visits],
                route=itinerary_data["route"],
                itinerary_text=itinerary_text,
                itinerary_data=itinerary_data
            )
            
            state["final_itinerary"] = {
                "itinerary": new_itinerary,
                "travel_plan": travel_plan,
                "saved": save_success,
                "selected_cities_count": len(selected_cities),
                "total_available_count": len(all_available_sites)
            }
            
            state["step"] = "new_itinerary_created"
            return state
            
        except Exception as e:
            logger.error(f"Error creando nuevo itinerario: {e}")
            state["error"] = str(e)
            state["step"] = "error"
            return state
    
    async def _generate_response(self, state: SmartItineraryState) -> SmartItineraryState:
        """
        Genera la respuesta final para el usuario.
        """
        try:
            state["step"] = "generate_response"
            
            # Crear respuesta final
            response = self._create_smart_response(state)
            
            # Agregar respuesta final
            state["messages"].append(
                AIMessage(content=response)
            )
            
            return state
            
        except Exception as e:
            state["error"] = f"Error generando respuesta: {str(e)}"
            return state
    
    async def _handle_error(self, state: SmartItineraryState) -> SmartItineraryState:
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
    
    def _create_smart_response(self, state: SmartItineraryState) -> str:
        """
        Crea la respuesta final inteligente.
        """
        try:
            if state["existing_itinerary"].get("exists"):
                # Respuesta para itinerario modificado
                final_itinerary = state.get("final_itinerary", {})
                # Mostrar el itinerario actualizado si existe
                itinerary = final_itinerary.get("itinerary")
                if itinerary and isinstance(itinerary, dict):
                    return itinerary.get("itinerary", "Itinerario modificado correctamente.")
                return "¡Tu itinerario ha sido actualizado exitosamente!"
            else:
                # Respuesta para nuevo itinerario
                final_itinerary = state.get("final_itinerary", {})
                message = final_itinerary.get("message")
                if message:
                    return message
                itinerary = final_itinerary.get("itinerary")
                if itinerary and isinstance(itinerary, dict):
                    return itinerary.get("itinerary", "Itinerario creado correctamente.")
                return "¡Itinerario creado exitosamente!"
        except Exception as e:
            return f"Error generando respuesta final: {str(e)}"
    
    async def _save_itinerary_to_database(self, user_id: str, travel_id: str, country: str, 
                                         cities: List[Dict[str, Any]], route: Dict[str, Any], 
                                         itinerary_text: str, itinerary_data: Dict[str, Any] = None) -> bool:
        """
        Guarda el itinerario en la base de datos con información de tiempo.
        """
        try:
            itineraries_collection = await get_itineraries_collection()
            
            # Usar itinerary_data si se proporciona, sino crear uno básico
            if itinerary_data:
                itinerary_to_save = itinerary_data
            else:
                # Preparar datos del itinerario (fallback)
                itinerary_to_save = {
                    "travel_id": travel_id,
                    "user_id": user_id,
                    "country": country,
                    "cities": cities,
                    "route": route,
                    "itinerary": itinerary_text,
                    "total_days": 7,  # Default
                    "exploration_days": 0,
                    "transport_days": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            # Guardar en la base de datos
            result = await itineraries_collection.insert_one(itinerary_to_save)
            
            if result.inserted_id:
                logger.info(f"Itinerario guardado exitosamente con ID: {result.inserted_id}")
                # Generaciones en background
                try:
                    asyncio.create_task(daily_visits_service.generate_and_save_for_travel(travel_id))
                except Exception as e:
                    logger.error(f"Error scheduling daily_visits generation: {e}")
                try:
                    asyncio.create_task(hotel_suggestions_service.generate_and_save_for_travel(travel_id))
                except Exception as e:
                    logger.error(f"Error scheduling hotel_suggestions generation: {e}")
                logger.info(f"Ciudades incluidas: {len(cities)}")
                logger.info(f"Días totales: {itinerary_to_save.get('total_days', 0)}")
                logger.info(f"Días de exploración: {itinerary_to_save.get('exploration_days', 0)}")
                logger.info(f"Días de transporte: {itinerary_to_save.get('transport_days', 0)}")
                return True
            else:
                logger.error("Error guardando itinerario: No se obtuvo ID")
                return False
                
        except Exception as e:
            logger.error(f"Error guardando itinerario en BBDD: {e}")
            return False
    
    async def process_smart_request(self, user_input: str, user_id: str, travel_id: str, country: str) -> Dict[str, Any]:
        """
        Procesa una solicitud inteligente del usuario usando selección de destinos ANTES del grafo.
        """
        try:
            logger.info(f"Procesando solicitud inteligente: {user_input}")
            # Determinar días efectivos del viaje: priorizar configuración del viaje en BBDD
            effective_total_days = None
            try:
                travels = await get_travels_collection()
                tr = await travels.find_one({"_id": ObjectId(travel_id)})
                if tr and tr.get("total_days"):
                    effective_total_days = int(tr.get("total_days"))
            except Exception as e:
                logger.warning(f"No se pudo leer total_days del viaje {travel_id}: {e}")
            # Gating defensivo: no crear/modificar ante saludos o entradas vacías
            lowered = (user_input or "").strip().lower()
            greetings = {"hola", "hola!", "hola :)", "hi", "hello", "buenas", "buenos dias", "buenas tardes", "buenas noches"}
            if lowered in greetings or len(lowered) <= 2:
                return {
                    "message": (
                        "¡Hola! ¿Quieres que te cree un itinerario o modificar uno existente? "
                        "Dime país y duración (por ejemplo, 14 días) y el estilo (playa, historia, naturaleza, gastronomía)."
                    ),
                    "is_user": False,
                    "intention": "clarify",
                    "workflow_state": {"step": "gated", "existing_itinerary": False}
                }
            
            # Detectar itinerario existente
            existing_itinerary = await self.detection_agent.detect_existing_itinerary(user_id, travel_id)
            
            if existing_itinerary.get("exists"):
                # Modificar itinerario existente
                logger.info("Itinerario existente detectado, modificando...")
                
                # Analizar la solicitud
                analysis = await self.modification_agent.analyze_modification_request(user_input)
                
                # Obtener sitios disponibles
                available_sites = await self.db_agent.search_cities_by_country(country or "thailand")
                
                # Aplicar modificaciones
                modifications = await self.modification_agent.apply_modifications(
                    existing_itinerary, analysis, available_sites
                )
                
                # Si la modificación fue exitosa y hay cambios, devolver el itinerario actualizado
                if modifications.get("success") and modifications.get("itinerary"):
                    updated_itinerary = modifications["itinerary"]
                    cities_list = updated_itinerary.get("cities", [])
                    
                    # Crear mensaje con el itinerario actualizado
                    cities_text = "\n".join([
                        f"• {city.get('name', 'Sin nombre')} ({city.get('days', 1)} días)"
                        for city in cities_list
                    ])
                    
                    total_cities = len(cities_list)
                    plural = "ciudad" if total_cities == 1 else "ciudades"
                    response_message = f"""
¡Perfecto! He actualizado tu itinerario.

🗺️ ITINERARIO ACTUALIZADO:
{cities_text}

Total: {total_cities} {plural}
"""
                else:
                    response_message = modifications.get("message", "No se realizaron cambios en el itinerario.")
            else:
                # ⭐ CREAR NUEVO ITINERARIO CON SELECCIÓN ANTES DEL GRAFO
                logger.info("Creando nuevo itinerario con selección inteligente...")
                
                # Calcular días totales efectivos: usar BBDD si existe, si no extraer del mensaje, si no default 7
                extracted_days = self._extract_days_from_message(user_input)
                total_days = int(effective_total_days or extracted_days or 7)
                logger.info(f"Días totales efectivos para la selección: {total_days}")
                
                # ⭐ IA SELECCIONA DESTINOS ANTES DEL GRAFO
                destination_selection = await destination_selection_agent.select_destinations(
                    country=country or "thailand",
                    total_days=total_days,
                    user_preferences=None
                )
                
                # Obtener SOLO las ciudades seleccionadas por la IA
                selected_cities = destination_selection.get("selected_cities", [])
                
                if not selected_cities:
                    response_message = "Lo siento, no pude seleccionar destinos apropiados para tu viaje."
                else:
                    logger.info(f"IA seleccionó {len(selected_cities)} destinos")
                    
                    # ⭐ NUEVO: Usar TimeBudgetScheduler para crear plan temporal
                    start_dt = datetime.utcnow()
                    scheduler = TimeBudgetScheduler(total_days, start_dt)
                    
                    # Crear matriz de transporte
                    transport_matrix = scheduler.create_transport_matrix(selected_cities)
                    
                    # Crear plan de viaje con tiempos reales
                    travel_plan = scheduler.allocate_time(selected_cities, transport_matrix)
                    
                    # Asignar IDs del estado
                    travel_plan.travel_id = travel_id
                    travel_plan.user_id = user_id
                    
                    # ⭐ NUEVO: Usar PromptBuilder para generar prompt unificado
                    prompt_builder = PromptBuilder()
                    itinerary_prompt = prompt_builder.build_itinerary_prompt(travel_plan, country or "thailand")
                    
                    # Generar itinerario usando el prompt unificado
                    new_itinerary = self._generate_itinerary_with_unified_prompt(itinerary_prompt)
                    
                    # Extraer el itinerario generado por IA
                    itinerary_text = new_itinerary.get("itinerary", "No se pudo generar el itinerario")
                    
                    # Preparar datos del itinerario con información de tiempo
                    itinerary_data = {
                        "travel_id": travel_id,
                        "user_id": user_id,
                        "country": country or "thailand",
                        "cities": [visit.dict() for visit in travel_plan.visits],
                        "route": {
                            "total_distance": 0,  # Se calculará después si es necesario
                            "estimated_time": travel_plan.total_travel_hours,
                            "algorithm": "time_budget_scheduler"
                        },
                        "itinerary": itinerary_text,
                        "total_days": total_days,
                        "exploration_days": travel_plan.total_explore_hours / 24,
                        "transport_days": travel_plan.total_travel_hours / 24,
                        "travel_plan": travel_plan.dict(),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    # GUARDAR EL ITINERARIO EN LA BBDD
                    save_success = await self._save_itinerary_to_database(
                        user_id=user_id,
                        travel_id=travel_id,
                        country=country or "thailand",
                        cities=[visit.dict() for visit in travel_plan.visits],
                        route=itinerary_data["route"],
                        itinerary_text=itinerary_text,
                        itinerary_data=itinerary_data
                    )
                    
                    if save_success:
                        logger.info("Itinerario guardado exitosamente en la BBDD")
                        logger.info(f"Ciudades incluidas: {len(selected_cities)}")
                        logger.info(f"Días totales: {total_days}, Horas exploración: {travel_plan.total_explore_hours:.1f}")
                    else:
                        logger.error("Error guardando itinerario en la BBDD")
                    
                    response_message = itinerary_text

                    # Generar daily_visits para el viaje creado
                    try:
                        await daily_visits_service.generate_and_save_for_travel(travel_id)
                    except Exception as e:
                        logger.error(f"Error generating daily_visits: {e}")
            
            return {
                "message": response_message,
                "is_user": False,
                "intention": "itinerary_modified" if existing_itinerary.get("exists") else "itinerary_created",
                "workflow_state": {
                    "step": "completed",
                    "existing_itinerary": bool(existing_itinerary.get("exists")),
                    "modifications_applied": bool(existing_itinerary.get("exists")),
                    "selected_cities_count": len(selected_cities) if 'selected_cities' in locals() else 0,
                    "total_available_count": len(all_available_sites) if 'all_available_sites' in locals() else 0,
                    "error": ""
                }
            }
            
        except Exception as e:
            logger.error(f"Error en el flujo inteligente: {e}")
            return {
                "message": f"Lo siento, hubo un error procesando tu solicitud: {str(e)}",
                "is_user": False,
                "intention": "error"
            }

    def _extract_days_from_message(self, message: str) -> int:
        """
        Extrae el número de días del mensaje del usuario.
        """
        import re
        
        # Buscar patrones como "7 días", "una semana", etc.
        patterns = [
            r'(\d+)\s*días?',
            r'(\d+)\s*days?',
            r'una semana',
            r'one week',
            r'(\d+)\s*semanas?',
            r'(\d+)\s*weeks?',
            r'fin de semana',
            r'weekend',
            r'pocos días',
            r'few days',
            r'varios días',
            r'several days'
        ]
        
        message_lower = message.lower()
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                if 'semana' in pattern or 'week' in pattern:
                    if 'una' in pattern or 'one' in pattern:
                        return 7
                    else:
                        return int(match.group(1)) * 7
                elif 'fin de semana' in pattern or 'weekend' in pattern:
                    return 3
                elif 'pocos días' in pattern or 'few days' in pattern:
                    return 3
                elif 'varios días' in pattern or 'several days' in pattern:
                    return 5
                else:
                    return int(match.group(1))
        
        # Si no se encuentra información específica, analizar el contexto
        context_keywords = {
            'corto': 3,
            'short': 3,
            'rápido': 3,
            'quick': 3,
            'largo': 14,
            'long': 14,
            'extenso': 21,
            'extensive': 21,
            'vacaciones': 10,
            'vacation': 10,
            'viaje': 7,
            'trip': 7
        }
        
        for keyword, days in context_keywords.items():
            if keyword in message_lower:
                return days
        
        # Default basado en el país (algunos países requieren más tiempo)
        return 7  # Default conservador

    def _generate_itinerary_with_unified_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Genera itinerario usando el prompt unificado.
        """
        try:
            from openai import AzureOpenAI
            from app.config import settings
            
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en viajes y turismo. Tu tarea es crear itinerarios detallados y atractivos.

INSTRUCCIONES:
1. Crea itinerarios realistas y prácticos
2. Incluye actividades específicas para cada ciudad
3. Considera el tiempo de viaje entre ciudades
4. Sugiere lugares de interés, restaurantes y actividades
5. Mantén un tono conversacional y atractivo
6. Incluye consejos prácticos de viaje
7. Considera la cultura y características del país

FORMATO DE RESPUESTA:
- Usa un formato claro y estructurado
- Incluye días numerados
- Menciona actividades específicas
- Incluye consejos de transporte
- Sugiere lugares de interés
"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            itinerary_text = response.choices[0].message.content
            
            return {
                "itinerary": itinerary_text,
                "summary": {
                    "generated_with": "unified_prompt",
                    "prompt_length": len(prompt)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando itinerario con prompt unificado: {e}")
            return {
                "itinerary": "No se pudo generar el itinerario",
                "error": str(e)
            } 