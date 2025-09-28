"""
Agente especializado en detectar y gestionar itinerarios existentes.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from app.database import get_itineraries_collection, get_itinerary_items_collection
from app.models.travel import Itinerary, ItineraryItem

logger = logging.getLogger(__name__)

class ItineraryDetectionAgent:
    """
    Agente que detecta y gestiona itinerarios existentes.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def detect_existing_itinerary(self, user_id: str, travel_id: str) -> Optional[Dict[str, Any]]:
        """
        Detecta si existe un itinerario para el viaje del usuario.
        """
        try:
            itineraries_collection = await get_itineraries_collection()
            
            # Buscar itinerario existente
            # Detectar por travel_id. Si hay múltiples, tomar el más reciente
            cursor = itineraries_collection.find({
                "travel_id": travel_id
            }).sort("updated_at", -1)
            results = await cursor.to_list(length=1)
            existing_itinerary = results[0] if results else None
            
            if existing_itinerary:
                # Obtener items del itinerario
                items_collection = await get_itinerary_items_collection()
                items = await items_collection.find({
                    "itinerary_id": str(existing_itinerary["_id"])
                }).sort("day", 1).to_list(length=None)
                
                return {
                    "exists": True,
                    "itinerary": existing_itinerary,
                    "items": items,
                    "total_items": len(items),
                    "created_at": existing_itinerary.get("created_at"),
                    "updated_at": existing_itinerary.get("updated_at")
                }
            else:
                return {
                    "exists": False,
                    "itinerary": None,
                    "items": [],
                    "total_items": 0
                }
                
        except Exception as e:
            self.logger.error(f"Error detectando itinerario: {e}")
            return None
    
    async def analyze_user_request(self, user_message: str, existing_itinerary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza la petición del usuario para determinar qué modificación hacer.
        """
        try:
            # Extraer información del itinerario existente
            current_items = existing_itinerary.get("items", [])
            current_cities = [item.get("city_name") for item in current_items if item.get("city_name")]
            
            # Analizar el mensaje del usuario
            analysis = {
                "action_type": self._determine_action_type(user_message),
                "cities_to_add": self._extract_cities_to_add(user_message),
                "cities_to_remove": self._extract_cities_to_remove(user_message, current_cities),
                "preferences_changed": self._extract_preferences(user_message),
                "duration_changed": self._extract_duration_change(user_message),
                "priority_changed": self._extract_priority_change(user_message)
            }
            
            return {
                "analysis": analysis,
                "current_itinerary": existing_itinerary,
                "modification_needed": any([
                    analysis["cities_to_add"],
                    analysis["cities_to_remove"],
                    analysis["preferences_changed"],
                    analysis["duration_changed"],
                    analysis["priority_changed"]
                ])
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando petición: {e}")
            return {"error": str(e)}
    
    def _determine_action_type(self, message: str) -> str:
        """
        Determina el tipo de acción que quiere hacer el usuario.
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["añadir", "agregar", "add", "incluir"]):
            return "add_cities"
        elif any(word in message_lower for word in ["quitar", "eliminar", "remove", "borrar"]):
            return "remove_cities"
        elif any(word in message_lower for word in ["cambiar", "modificar", "change", "update"]):
            return "modify_itinerary"
        elif any(word in message_lower for word in ["rehacer", "crear nuevo", "new", "nuevo"]):
            return "recreate_itinerary"
        elif any(word in message_lower for word in ["optimizar", "mejorar", "optimize"]):
            return "optimize_itinerary"
        else:
            return "unknown"
    
    def _extract_cities_to_add(self, message: str) -> List[str]:
        """
        Extrae las ciudades que el usuario quiere añadir.
        """
        # Implementar lógica de extracción de ciudades
        # Por ahora, retornar lista vacía
        return []
    
    def _extract_cities_to_remove(self, message: str, current_cities: List[str]) -> List[str]:
        """
        Extrae las ciudades que el usuario quiere quitar.
        """
        # Implementar lógica de extracción de ciudades a quitar
        return []
    
    def _extract_preferences(self, message: str) -> Dict[str, Any]:
        """
        Extrae las preferencias del usuario.
        """
        preferences = {}
        message_lower = message.lower()
        
        # Detectar preferencias de presupuesto
        if any(word in message_lower for word in ["barato", "económico", "low budget"]):
            preferences["budget"] = "low"
        elif any(word in message_lower for word in ["lujo", "premium", "high end"]):
            preferences["budget"] = "high"
        
        # Detectar preferencias de actividades
        if any(word in message_lower for word in ["cultura", "museos", "historia"]):
            preferences["activities"] = "cultural"
        elif any(word in message_lower for word in ["naturaleza", "aventura", "outdoor"]):
            preferences["activities"] = "adventure"
        elif any(word in message_lower for word in ["gastronomía", "comida", "restaurantes"]):
            preferences["activities"] = "food"
        
        return preferences
    
    def _extract_duration_change(self, message: str) -> Optional[int]:
        """
        Extrae cambios en la duración del viaje.
        """
        # Implementar lógica de extracción de duración
        return None
    
    def _extract_priority_change(self, message: str) -> Dict[str, Any]:
        """
        Extrae cambios en las prioridades del viaje.
        """
        # Implementar lógica de extracción de prioridades
        return {}
    
    async def get_available_sites_for_modification(self, country_code: str, current_cities: List[str]) -> Dict[str, Any]:
        """
        Obtiene sitios disponibles para modificar el itinerario.
        """
        try:
            from app.agents.database_agent import DatabaseAgent
            
            db_agent = DatabaseAgent()
            
            # Obtener todos los sitios del país
            all_sites = await db_agent.search_cities_by_country(country_code)
            
            # Filtrar sitios que no están en el itinerario actual
            available_sites = []
            for site in all_sites:
                if site.get("name") not in current_cities:
                    available_sites.append(site)
            
            return {
                "available_sites": available_sites,
                "total_available": len(available_sites),
                "current_cities": current_cities,
                "country_code": country_code
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo sitios disponibles: {e}")
            return {
                "available_sites": [],
                "total_available": 0,
                "error": str(e)
            }
    
    async def suggest_modifications(self, analysis: Dict[str, Any], available_sites: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sugiere modificaciones basadas en el análisis y sitios disponibles.
        """
        try:
            suggestions = {
                "cities_to_add": [],
                "cities_to_remove": [],
                "route_optimization": False,
                "duration_adjustment": False,
                "preference_updates": {}
            }
            
            # Analizar qué ciudades añadir
            if analysis.get("action_type") == "add_cities":
                # Sugerir ciudades basadas en preferencias y disponibilidad
                suggestions["cities_to_add"] = self._suggest_cities_to_add(
                    analysis, available_sites
                )
            
            # Analizar optimización de ruta
            if len(analysis.get("cities_to_add", [])) > 0:
                suggestions["route_optimization"] = True
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error sugiriendo modificaciones: {e}")
            return {"error": str(e)}
    
    def _suggest_cities_to_add(self, analysis: Dict[str, Any], available_sites: Dict[str, Any]) -> List[str]:
        """
        Sugiere ciudades para añadir basándose en preferencias.
        """
        suggestions = []
        preferences = analysis.get("preferences_changed", {})
        available = available_sites.get("available_sites", [])
        
        # Filtrar por preferencias
        for site in available:
            if self._matches_preferences(site, preferences):
                suggestions.append(site.get("name"))
        
        # Limitar a 3 sugerencias
        return suggestions[:3]
    
    def _matches_preferences(self, site: Dict[str, Any], preferences: Dict[str, Any]) -> bool:
        """
        Verifica si un sitio coincide con las preferencias del usuario.
        """
        # Implementar lógica de matching
        return True  # Por ahora, retornar True 