"""
Builder unificado para prompts de itinerarios basado en TravelPlan.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
from .scheduler import TravelPlan, CityVisit

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Constructor de prompts unificado para itinerarios.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_itinerary_prompt(self, plan: TravelPlan, country: str) -> str:
        """
        Construye prompt para generar itinerario detallado.
        """
        try:
            # Formatear información de ciudades con tiempos
            cities_info = self._format_cities_with_times(plan.visits)
            
            # Calcular estadísticas
            total_days = (plan.end_dt - plan.start_dt).days
            total_cities = len(plan.visits)
            
            prompt = f"""
Crea un itinerario detallado para un viaje a {country}.

INFORMACIÓN DEL VIAJE:
- País: {country}
- Fecha de inicio: {plan.start_dt.strftime('%d/%m/%Y %H:%M')}
- Fecha de fin: {plan.end_dt.strftime('%d/%m/%Y %H:%M')}
- Duración total: {total_days} días
- Ciudades a visitar: {total_cities}
- Horas de exploración: {plan.total_explore_hours:.1f}h
- Horas de transporte: {plan.total_travel_hours:.1f}h

CIUDADES CON HORARIOS:
{cities_info}

PREFERENCIAS DEL USUARIO:
{self._format_preferences(plan.preferences)}

REQUERIMIENTOS:
1. Crea un itinerario día por día con horarios específicos
2. Incluye actividades detalladas para cada ciudad
3. Sugiere lugares específicos con nombres y direcciones
4. Incluye recomendaciones de restaurantes y hoteles
5. Considera las preferencias del usuario
6. Incluye consejos de transporte detallados
7. Añade información cultural e histórica
8. Sugiere actividades alternativas
9. Incluye presupuesto estimado
10. Considera clima y temporada

FORMATO ESPECÍFICO:
- Día X: [Nombre ciudad] - [Fecha llegada] a [Fecha salida]
  - [Hora llegada] - [Actividad específica con detalles]
  - [Hora almuerzo] - [Restaurante con nombre y tipo de comida]
  - [Hora tarde] - [Lugar de interés con información]
  - [Hora noche] - [Cena y actividades nocturnas]
  
- Transporte: [Detalles de transporte a siguiente ciudad]
- Consejos del día: [Consejos específicos]
- Presupuesto estimado: [Cantidad]
- Información cultural: [Datos culturales]
"""
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error construyendo prompt: {e}")
            return self._build_fallback_prompt(country, plan.visits)
    
    def build_modification_prompt(self, plan: TravelPlan, user_request: str) -> str:
        """
        Construye prompt para analizar modificaciones.
        """
        try:
            current_cities = self._format_cities_for_modification(plan.visits)
            
            prompt = f"""
Analiza la solicitud de modificación del usuario y sugiere cambios al itinerario.

SOLICITUD DEL USUARIO: "{user_request}"

ITINERARIO ACTUAL:
{current_cities}

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
            "score": número de relevancia (1-10),
            "type": "tipo de sitio",
            "description": "descripción"
        }}
    ],
    "message": "mensaje explicativo de los cambios"
}}
"""
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error construyendo prompt de modificación: {e}")
            return ""
    
    def _format_cities_with_times(self, visits: List[CityVisit]) -> str:
        """
        Formatea ciudades con información de tiempos.
        """
        cities_info = []
        
        for i, visit in enumerate(visits, 1):
            # Calcular días de estancia
            stay_days = visit.stay_hours / 24
            
            # Formatear fechas
            arrival_str = visit.arrival_dt.strftime("%d/%m %H:%M")
            departure_str = visit.departure_dt.strftime("%d/%m %H:%M")
            
            city_info = f"{i}. {visit.name}"
            city_info += f" (Llegada: {arrival_str}, Salida: {departure_str}, Estancia: {stay_days:.1f} días)"
            
            # Añadir información adicional
            if visit.metadata.get("population"):
                city_info += f" (Población: {visit.metadata['population']:,})"
            
            if visit.metadata.get("type"):
                city_info += f" - Tipo: {visit.metadata['type']}"
            
            if visit.metadata.get("description"):
                city_info += f" - {visit.metadata['description']}"
            
            # Añadir transporte a siguiente ciudad
            if visit.transport_hours_from_prev > 0:
                city_info += f" - Transporte desde anterior: {visit.transport_hours_from_prev:.1f}h"
            
            cities_info.append(city_info)
        
        return "\n".join(cities_info)
    
    def _format_cities_for_modification(self, visits: List[CityVisit]) -> str:
        """
        Formatea ciudades para análisis de modificaciones.
        """
        cities_info = []
        
        for visit in visits:
            stay_days = visit.stay_hours / 24
            city_info = {
                "name": visit.name,
                "days": stay_days,
                "type": visit.metadata.get("type", ""),
                "description": visit.metadata.get("description", ""),
                "score": visit.metadata.get("score", 1)
            }
            cities_info.append(city_info)
        
        return str(cities_info)
    
    def _format_preferences(self, preferences: Dict[str, Any]) -> str:
        """
        Formatea preferencias del usuario.
        """
        if not preferences:
            return "No se especificaron preferencias"
        
        pref_list = []
        for key, value in preferences.items():
            pref_list.append(f"- {key}: {value}")
        
        return "\n".join(pref_list)
    
    def _build_fallback_prompt(self, country: str, visits: List[CityVisit]) -> str:
        """
        Prompt de respaldo si hay error en el principal.
        """
        cities_text = "\n".join([f"- {visit.name}" for visit in visits])
        
        return f"""
Crea un itinerario para un viaje a {country}.

CIUDADES A VISITAR:
{cities_text}

Crea un itinerario día por día con actividades específicas para cada ciudad.
""" 