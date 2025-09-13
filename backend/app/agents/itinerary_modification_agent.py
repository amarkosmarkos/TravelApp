"""
Agente especializado en modificar itinerarios existentes.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from app.database import get_itineraries_collection, get_itinerary_items_collection
from app.models.travel import Itinerary, ItineraryItem
from bson import ObjectId
import json
from pydantic import BaseModel, ValidationError
from app.services.daily_visits_service import daily_visits_service

logger = logging.getLogger(__name__)

class ItineraryModificationAgent:
    """
    Agente que modifica itinerarios existentes.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def modify_itinerary(self, 
                              itinerary_id: str,
                              modifications: Dict[str, Any],
                              user_id: str) -> Dict[str, Any]:
        """
        Modifica un itinerario existente según las especificaciones.
        """
        try:
            # Obtener el itinerario actual
            itineraries_collection = await get_itineraries_collection()
            current_itinerary = await itineraries_collection.find_one({
                "_id": ObjectId(itinerary_id),
                "user_id": user_id
            })
            
            if not current_itinerary:
                return {"error": "Itinerario no encontrado"}
            
            # Aplicar modificaciones
            modified_itinerary = await self._apply_modifications(
                current_itinerary, modifications
            )
            
            # Actualizar en la base de datos
            result = await itineraries_collection.update_one(
                {"_id": ObjectId(itinerary_id)},
                {
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "modifications": modifications,
                        "total_items": len(modified_itinerary.get("items", [])),
                        "last_modified_by": user_id
                    }
                }
            )
            
            # Actualizar items del itinerario
            await self._update_itinerary_items(itinerary_id, modified_itinerary.get("items", []))
            
            return {
                "success": True,
                "itinerary_id": itinerary_id,
                "modifications_applied": modifications,
                "total_items": len(modified_itinerary.get("items", [])),
                "updated_at": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error modificando itinerario: {e}")
            return {"error": str(e)}
    
    async def _apply_modifications(self, current_itinerary: Dict[str, Any], 
                                 modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica las modificaciones al itinerario actual.
        """
        try:
            current_items = current_itinerary.get("items", [])
            modified_items = current_items.copy()
            
            # Aplicar cambios según el tipo de modificación
            if modifications.get("action_type") == "add_cities":
                modified_items = await self._add_cities_to_itinerary(
                    current_items, modifications.get("cities_to_add", [])
                )
            
            elif modifications.get("action_type") == "remove_cities":
                modified_items = await self._remove_cities_from_itinerary(
                    current_items, modifications.get("cities_to_remove", [])
                )
            
            elif modifications.get("action_type") == "optimize_itinerary":
                modified_items = await self._optimize_itinerary_route(current_items)
            
            elif modifications.get("action_type") == "update_preferences":
                modified_items = await self._update_itinerary_preferences(
                    current_items, modifications.get("preferences", {})
                )
            
            # Recalcular días y orden
            modified_items = self._recalculate_itinerary_days(modified_items)
            
            return {
                **current_itinerary,
                "items": modified_items,
                "total_items": len(modified_items),
                "last_modification": modifications
            }
            
        except Exception as e:
            self.logger.error(f"Error aplicando modificaciones: {e}")
            return current_itinerary
    
    async def _add_cities_to_itinerary(self, current_items: List[Dict], 
                                      cities_to_add: List[str]) -> List[Dict]:
        """
        Añade ciudades al itinerario.
        """
        try:
            from app.agents.database_agent import DatabaseAgent
            from app.agents.routing_agent import RoutingAgent
            
            db_agent = DatabaseAgent()
            routing_agent = RoutingAgent()
            
            # Obtener información de las ciudades a añadir
            new_items = []
            for city_name in cities_to_add:
                # Buscar información de la ciudad
                city_info = await db_agent.search_sites_by_city(city_name)
                if city_info:
                    new_items.append({
                        "city_name": city_name,
                        "city_id": city_info[0].get("id"),
                        "day": len(current_items) + len(new_items) + 1,
                        "activities": [],
                        "accommodation": "",
                        "transport": "",
                        "notes": f"Añadido por modificación del usuario"
                    })
            
            # Combinar items actuales con nuevos
            all_items = current_items + new_items
            
            # Optimizar ruta si hay múltiples ciudades
            if len(all_items) > 1:
                # Convertir a formato para routing
                cities_for_routing = [
                    {"name": item["city_name"]} for item in all_items
                ]
                
                # Calcular ruta optimizada
                optimized_route = routing_agent.calculate_route(cities_for_routing)
                
                # Reordenar items según la ruta optimizada
                optimized_items = []
                for i, city in enumerate(optimized_route.get("route", [])):
                    # Encontrar el item correspondiente
                    for item in all_items:
                        if item["city_name"] == city["name"]:
                            item["day"] = i + 1
                            optimized_items.append(item)
                            break
                
                return optimized_items
            
            return all_items
            
        except Exception as e:
            self.logger.error(f"Error añadiendo ciudades: {e}")
            return current_items
    
    async def _remove_cities_from_itinerary(self, current_items: List[Dict], 
                                           cities_to_remove: List[str]) -> List[Dict]:
        """
        Elimina ciudades del itinerario.
        """
        try:
            # Filtrar items que no están en la lista de eliminación
            remaining_items = [
                item for item in current_items 
                if item.get("city_name") not in cities_to_remove
            ]
            
            # Recalcular días
            for i, item in enumerate(remaining_items):
                item["day"] = i + 1
            
            return remaining_items
            
        except Exception as e:
            self.logger.error(f"Error eliminando ciudades: {e}")
            return current_items
    
    async def _optimize_itinerary_route(self, current_items: List[Dict]) -> List[Dict]:
        """
        Optimiza la ruta del itinerario.
        """
        try:
            from app.agents.routing_agent import RoutingAgent
            
            routing_agent = RoutingAgent()
            
            # Convertir a formato para routing
            cities_for_routing = [
                {"name": item["city_name"]} for item in current_items
            ]
            
            # Calcular ruta optimizada
            optimized_route = routing_agent.calculate_route(cities_for_routing)
            
            # Reordenar items según la ruta optimizada
            optimized_items = []
            for i, city in enumerate(optimized_route.get("route", [])):
                # Encontrar el item correspondiente
                for item in current_items:
                    if item["city_name"] == city["name"]:
                        item["day"] = i + 1
                        optimized_items.append(item)
                        break
            
            return optimized_items
            
        except Exception as e:
            self.logger.error(f"Error optimizando ruta: {e}")
            return current_items
    
    async def _update_itinerary_preferences(self, current_items: List[Dict], 
                                          preferences: Dict[str, Any]) -> List[Dict]:
        """
        Actualiza las preferencias del itinerario.
        """
        try:
            # Actualizar items con nuevas preferencias
            for item in current_items:
                item["preferences"] = preferences
                item["last_updated"] = datetime.utcnow()
            
            return current_items
            
        except Exception as e:
            self.logger.error(f"Error actualizando preferencias: {e}")
            return current_items
    
    def _recalculate_itinerary_days(self, items: List[Dict]) -> List[Dict]:
        """
        Recalcula los días del itinerario.
        """
        try:
            from datetime import datetime, timedelta
            from geopy.distance import geodesic
            AVG_SPEED_KMH = 70
            # Determinar fecha de inicio: llegada de la primera ciudad o ahora
            if items and items[0].get("arrival_dt"):
                current_dt = datetime.fromisoformat(items[0]["arrival_dt"])
            else:
                current_dt = datetime.utcnow()
            for i, item in enumerate(items):
                item["day"] = i + 1
                stay_days = item.get("days") or item.get("stay_days") or 1
                # Asignar arrival si no existe o si estamos recalculando
                item["arrival_dt"] = current_dt.isoformat()
                departure_dt = current_dt + timedelta(days=stay_days)
                item["departure_dt"] = departure_dt.isoformat()
                # Calcular transporte a siguiente
                if i < len(items) - 1:
                    next_item = items[i + 1]
                    if (item.get("latitude") or item.get("lat")) and (item.get("longitude") or item.get("lon")) and (next_item.get("latitude") or next_item.get("lat")) and (next_item.get("longitude") or next_item.get("lon")):
                        lat1 = item.get("latitude") or item.get("lat")
                        lon1 = item.get("longitude") or item.get("lon")
                        lat2 = next_item.get("latitude") or next_item.get("lat")
                        lon2 = next_item.get("longitude") or next_item.get("lon")
                        dist_km = geodesic((lat1, lon1), (lat2, lon2)).kilometers
                        travel_hours = dist_km / AVG_SPEED_KMH
                    else:
                        travel_hours = 4
                else:
                    travel_hours = 0
                item["transport_hours_to_next"] = travel_hours
                current_dt = departure_dt + timedelta(hours=travel_hours)
                item["updated_at"] = datetime.utcnow()
            return items
            
        except Exception as e:
            self.logger.error(f"Error recalculando días: {e}")
            return items
    
    async def _update_itinerary_items(self, itinerary_id: str, items: List[Dict]):
        """
        Actualiza los items del itinerario en la base de datos.
        """
        try:
            items_collection = await get_itinerary_items_collection()
            
            # Eliminar items existentes
            await items_collection.delete_many({"itinerary_id": itinerary_id})
            
            # Insertar nuevos items
            if items:
                for item in items:
                    item["itinerary_id"] = itinerary_id
                    item["created_at"] = datetime.utcnow()
                    item["updated_at"] = datetime.utcnow()
                
                await items_collection.insert_many(items)
            
        except Exception as e:
            self.logger.error(f"Error actualizando items: {e}")
    
    async def get_modification_history(self, itinerary_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de modificaciones de un itinerario.
        """
        try:
            itineraries_collection = await get_itineraries_collection()
            
            itinerary = await itineraries_collection.find_one({"_id": ObjectId(itinerary_id)})
            
            if itinerary:
                return {
                    "itinerary_id": itinerary_id,
                    "created_at": itinerary.get("created_at"),
                    "updated_at": itinerary.get("updated_at"),
                    "modifications": itinerary.get("modifications", []),
                    "total_modifications": len(itinerary.get("modifications", []))
                }
            else:
                return {"error": "Itinerario no encontrado"}
                
        except Exception as e:
            self.logger.error(f"Error obteniendo historial: {e}")
            return {"error": str(e)} 
    
    async def analyze_modification_request(self, user_input: str) -> Dict[str, Any]:
        """
        Analiza la solicitud de modificación del usuario.
        """
        try:
            # Análisis básico de la intención
            user_input_lower = user_input.lower()
            
            # Detectar tipo de modificación
            if any(word in user_input_lower for word in ["añadir", "agregar", "add", "añade", "agrega"]):
                intention = "add_cities"
            elif any(word in user_input_lower for word in ["quitar", "eliminar", "remove", "quit", "borrar"]):
                intention = "remove_cities"
            elif any(word in user_input_lower for word in ["optimizar", "optimize", "mejorar", "improve"]):
                intention = "optimize_route"
            elif any(word in user_input_lower for word in ["cambiar", "modificar", "change", "modify"]):
                intention = "modify_preferences"
            else:
                intention = "general_modification"
            
            # Extraer ciudades mencionadas (implementación básica)
            cities_mentioned = []
            # Aquí podrías usar NLP para extraer nombres de ciudades
            # Por ahora, devolvemos una lista vacía

            # Extraer días solicitados
            total_days = self._extract_days_from_text(user_input)

            # Extraer tema preferido (historia, playa, naturaleza, gastronomía)
            theme = self._extract_theme_from_text(user_input)
            
            return {
                "intention": intention,
                "cities_mentioned": cities_mentioned,
                "user_input": user_input,
                "total_days": total_days,
                "theme": theme,
                "analysis": {
                    "action_type": intention,
                    "confidence": 0.7,
                    "requires_user_confirmation": False,
                    "total_days": total_days,
                    "theme": theme
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando solicitud de modificación: {e}")
            return {
                "intention": "general_modification",
                "cities_mentioned": [],
                "user_input": user_input,
                "analysis": {
                    "action_type": "general_modification",
                    "confidence": 0.5,
                    "requires_user_confirmation": True
                }
            }

    def _extract_days_from_text(self, text: str) -> int:
        import re
        t = text.lower()
        patterns = [
            r"(\d+)\s*d[ií]as?",
            r"(\d+)\s*days?",
            r"una semana|one week",
            r"(\d+)\s*semanas?|(\d+)\s*weeks?",
            r"fin de semana|weekend"
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                if "semana" in p or "week" in p:
                    if "una" in p or "one" in p:
                        return 7
                    # tomar último grupo con número
                    num = next((int(g) for g in m.groups() if g and g.isdigit()), None)
                    if num:
                        return num * 7
                if "fin de semana" in p or "weekend" in p:
                    return 3
                if m.group(1):
                    return int(m.group(1))
        return 0

    def _extract_theme_from_text(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["historia", "histórico", "historico", "templo", "museo"]):
            return "history"
        if any(k in t for k in ["playa", "beach", "isla", "islas", "snorkel"]):
            return "beach"
        if any(k in t for k in ["naturaleza", "montaña", "parque", "senderismo", "trekking"]):
            return "nature"
        if any(k in t for k in ["comida", "gastronom", "restaurante", "food"]):
            return "food"
        return ""
    
    async def apply_modifications(self, existing_itinerary: Dict[str, Any], 
                                analysis: Dict[str, Any], available_sites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aplica modificaciones usando IA para entender la intención y hacer cambios inteligentes.
        """
        try:
            logger.info(f"=== INICIANDO apply_modifications ===")
            logger.info(f"existing_itinerary keys: {list(existing_itinerary.keys())}")
            logger.info(f"existing_itinerary: {existing_itinerary}")
            logger.info(f"analysis: {analysis}")
            logger.info(f"available_sites count: {len(available_sites)}")
            
            user_input = analysis.get("user_input", "")
            
            # Buscar el travel_id de diferentes maneras
            travel_id = (
                existing_itinerary.get("travel_id")
                or (existing_itinerary.get("itinerary", {}).get("travel_id") if isinstance(existing_itinerary.get("itinerary"), dict) else None)
                or existing_itinerary.get("_id")
                or existing_itinerary.get("id")
            )
            
            if not travel_id:
                logger.error(f"No se encontró travel_id en existing_itinerary")
                logger.error(f"Keys disponibles: {list(existing_itinerary.keys())}")
                return {
                    "success": False,
                    "error": "No se encontró el ID del viaje"
                }
            
            logger.info(f"Usando travel_id: {travel_id}")
            
            # Obtener el itinerario actual de la base de datos
            itineraries_collection = await get_itineraries_collection()
            current_itinerary = await itineraries_collection.find_one({
                "travel_id": travel_id
            })
            
            if not current_itinerary:
                logger.error(f"Itinerario no encontrado en BBDD para travel_id: {travel_id}")
                return {
                    "success": False,
                    "error": "Itinerario no encontrado"
                }
            
            # Obtener las ciudades actuales del itinerario
            current_cities = current_itinerary.get("cities", [])
            logger.info(f"Ciudades actuales del itinerario: {len(current_cities)}")
            
            # Usar IA para entender la modificación
            logger.info(f"Llamando a _analyze_modification_with_ai...")
            modification_result = await self._analyze_modification_with_ai(
                user_input, current_cities, available_sites
            )
            
            logger.info(f"Resultado de IA: {modification_result}")
            
            if modification_result.get("success"):
                # Aplicar los cambios sugeridos por la IA
                modified_cities = modification_result.get("modified_cities", current_cities)

                # Filtrar por tema si se solicitó (history/beach/nature/food)
                theme = analysis.get("theme") or analysis.get("analysis", {}).get("theme") or ""
                if theme:
                    theme_keywords = {
                        "history": ["temple", "templo", "museo", "ruins", "ruinas", "historic"],
                        "beach": ["beach", "playa", "island", "isla", "snorkel"],
                        "nature": ["park", "parque", "mountain", "montaña", "national"],
                        "food": ["food", "comida", "restaurant", "restaurante", "market", "mercado"]
                    }
                    keys = theme_keywords.get(theme, [])
                    def matches_theme(city: Dict[str, Any]) -> bool:
                        text = (city.get("description") or "") + " " + (city.get("type") or "") + " " + (city.get("name") or "")
                        t = text.lower()
                        return any(k in t for k in keys) if keys else True
                    # Mantener ciudades que encajan y, si quedan muy pocas, volver a incluir las originales
                    themed = [c for c in modified_cities if matches_theme(c)]
                    if len(themed) >= 2:
                        modified_cities = themed

                # Redistribuir días al total solicitado (si existe), manteniendo mínimo 1 día por ciudad
                requested_days = analysis.get("total_days") or analysis.get("analysis", {}).get("total_days") or 0
                if requested_days and requested_days > 0 and modified_cities:
                    per_city = max(1, requested_days // len(modified_cities))
                    remainder = max(0, requested_days - per_city * len(modified_cities))
                    for idx, city in enumerate(modified_cities):
                        base_days = per_city + (1 if idx < remainder else 0)
                        city["days"] = base_days

                # Si no hay days en las ciudades, asignar 2 por defecto y luego normalizar a <= 14
                if modified_cities and not any(c.get("days") for c in modified_cities):
                    for c in modified_cities:
                        c["days"] = 2

                # Normalizar claves de coordenadas
                for c in modified_cities:
                    if c.get("lat") and not c.get("latitude"):
                        c["latitude"] = c.get("lat")
                    if c.get("lon") and not c.get("longitude"):
                        c["longitude"] = c.get("lon")

                # Actualizar el itinerario en la base de datos
                await itineraries_collection.update_one(
                    {"travel_id": travel_id},
                    {
                        "$set": {
                            "cities": modified_cities,
                            "updated_at": datetime.utcnow(),
                            "total_items": len(modified_cities)
                        }
                    }
                )

                logger.info(f"Itinerario actualizado por IA: {len(modified_cities)} ciudades")

                # Regenerar daily_visits para el travel
                try:
                    await daily_visits_service.generate_and_save_for_travel(str(travel_id))
                except Exception as e:
                    self.logger.error(f"Error regenerating daily_visits: {e}")

                # Mensaje con pluralización correcta
                total_cities = len(modified_cities)
                plural = "ciudad" if total_cities == 1 else "ciudades"

                return {
                    "success": True,
                    "action": "ai_modification",
                    "message": modification_result.get("message", f"Itinerario actualizado por IA: {total_cities} {plural}"),
                    "itinerary": {
                        "cities": modified_cities,
                        "total_items": total_cities,
                        "updated_at": datetime.utcnow()
                    }
                }
            else:
                logger.error(f"Error en IA: {modification_result.get('error')}")
                return {
                    "success": False,
                    "error": modification_result.get("error", "No se pudo procesar la modificación")
                }
                
        except Exception as e:
            logger.error(f"Error aplicando modificaciones: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_modification_with_ai(self, user_input: str, current_cities: List[Dict], 
                                          available_sites: List[Dict]) -> Dict[str, Any]:
        """
        Usa IA para analizar la modificación y sugerir cambios.
        """
        try:
            logger.info(f"Analizando modificación con IA: {user_input}")
            logger.info(f"Ciudades actuales: {len(current_cities)}")
            logger.info(f"Sitios disponibles: {len(available_sites)}")
            
            from openai import AzureOpenAI
            from app.config import settings
            
            client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
            
            # Preparar datos para la IA
            current_cities_formatted = [
                {
                    "name": city.get("name", ""),
                    "days": city.get("days", 1),
                    "type": city.get("type", ""),
                    "description": city.get("description", "")
                }
                for city in current_cities
            ]
            
            available_sites_formatted = [
                {
                    "name": site.get("name", ""),
                    "type": site.get("type", ""),
                    "description": site.get("description", ""),
                    "coordinates": {
                        "latitude": float(site.get("lat", 0)) if site.get("lat") else 0,
                        "longitude": float(site.get("lon", 0)) if site.get("lon") else 0
                    }
                }
                for site in available_sites
            ]
            
            logger.info(f"Datos preparados para IA")
            
            # Crear prompt para la IA
            prompt = f"""
            Analiza la solicitud de modificación del usuario y sugiere cambios al itinerario.

            SOLICITUD DEL USUARIO: "{user_input}"

            ITINERARIO ACTUAL:
            {current_cities_formatted}

            SITIOS DISPONIBLES:
            {available_sites_formatted}

            INSTRUCCIONES:
            1. Entiende la intención del usuario (cambiar, añadir, quitar ciudades)
            2. Identifica las ciudades mencionadas
            3. Sugiere los cambios apropiados
            4. Mantén la coherencia del itinerario
            5. Considera las distancias y tiempo de transporte

            RESPONDE EN FORMATO JSON:
            {{
                "intention": "tipo de modificación (change, add, remove, optimize)",
                "changes": [
                    {{
                        "action": "add/remove/replace",
                        "city_name": "nombre de la ciudad",
                        "reason": "razón del cambio"
                    }}
                ],
                "modified_cities": [
                    {{
                        "name": "nombre de la ciudad",
                        "days": número de días,
                        "type": "tipo de sitio",
                        "description": "descripción"
                    }}
                ],
                "message": "mensaje explicativo de los cambios"
            }}
            """
            
            logger.info(f"Llamando a la IA...")
            
            # Llamar a la IA
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en planificación de viajes. Analiza las solicitudes de modificación de itinerarios y sugiere cambios inteligentes."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            logger.info(f"Respuesta de IA recibida")
            
            # Modelos Pydantic para validar salida
            class Change(BaseModel):
                action: str
                city_name: str
                reason: str | None = None

            class ModifiedCity(BaseModel):
                name: str
                days: int | float | None = None
                type: str | None = None
                description: str | None = None

            class ModResult(BaseModel):
                intention: str
                changes: List[Change] = []
                modified_cities: List[ModifiedCity] = []
                message: str | None = None

            # Procesar respuesta
            response_content = response.choices[0].message.content or ""
            logger.info(f"Contenido de respuesta raw: {response_content[:200]}...")

            # Eliminar posibles bloques markdown ```json ... ``` y validar JSON
            import re
            cleaned = re.sub(r"```[a-zA-Z]*", "", response_content).replace("```", "").strip()
            
            logger.info(f"Contenido limpiado: {cleaned[:200]}...")
            # Intentar parsear con tolerancia
            try:
                result_raw = json.loads(cleaned)
            except Exception:
                # Intentar extraer el primer bloque JSON entre llaves
                import re as _re
                match = _re.search(r"\{[\s\S]*\}", cleaned)
                if not match:
                    raise
                result_raw = json.loads(match.group(0))

            # Validar contra esquema
            try:
                validated = ModResult(**result_raw)
            except ValidationError as ve:
                logger.error(f"Respuesta IA inválida: {ve}")
                return {"success": False, "error": "Respuesta IA inválida"}
            
            # Aplicar los cambios sugeridos por la IA
            modified_cities = []
            
            for city_data in validated.modified_cities:
                # Buscar el sitio correspondiente en available_sites
                site_data = None
                for site in available_sites:
                    if site.get("name", "").lower() == (city_data.name or "").lower():
                        site_data = site.copy()
                        site_data["days"] = int(city_data.days) if city_data.days else 2
                        break
                
                if site_data:
                    modified_cities.append(site_data)
            
            logger.info(f"Ciudades modificadas: {len(modified_cities)}")
            
            return {
                "success": True,
                "modified_cities": modified_cities,
                "message": validated.message or "Itinerario actualizado por IA",
                "intention": validated.intention or "modification"
            }
            
        except Exception as e:
            logger.error(f"Error analizando modificación con IA: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            } 