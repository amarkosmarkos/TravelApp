"""
Agente especializado en generar itinerarios detallados usando IA.
"""

from typing import List, Dict, Any
from openai import AzureOpenAI
from app.config import settings
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ItineraryAgent:
    """
    Agente especializado en generar itinerarios detallados.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    
    def create_itinerary(self, country: str, cities: List[Dict[str, Any]], route: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un itinerario detallado basado en el país, ciudades y ruta.
        """
        try:
            # Preparar datos para la IA
            itinerary_data = {
                "country": country,
                "cities": cities,
                "route": route,
                "total_distance": route.get("total_distance", 0),
                "estimated_time": route.get("estimated_time", 0),
                "algorithm": route.get("algorithm", "unknown")
            }
            
            # Generar itinerario usando IA
            itinerary = self._generate_itinerary_with_ai(itinerary_data)
            
            # Crear estructura de respuesta
            response = {
                "itinerary": itinerary,
                "summary": {
                    "country": country,
                    "total_cities": len(cities),
                    "total_distance_km": route.get("total_distance", 0),
                    "estimated_time_hours": route.get("estimated_time", 0),
                    "route_algorithm": route.get("algorithm", "unknown")
                },
                "cities": cities,
                "route_details": route
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creando itinerario: {e}")
            return {
                "error": str(e),
                "itinerary": "No se pudo generar el itinerario",
                "summary": {
                    "country": country,
                    "total_cities": len(cities),
                    "error": True
                }
            }
    
    def _generate_itinerary_with_ai(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Genera el itinerario usando IA.
        """
        try:
            # Preparar prompt para la IA
            prompt = self._create_itinerary_prompt(itinerary_data)
            
            # Llamar a la IA
            response = self.client.chat.completions.create(
                model=self.deployment_name,
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
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generando itinerario con IA: {e}")
            return f"No se pudo generar el itinerario: {str(e)}"
    
    def _create_itinerary_prompt(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Crea el prompt para generar el itinerario.
        """
        country = itinerary_data["country"]
        cities = itinerary_data["cities"]
        route = itinerary_data["route"]
        total_distance = itinerary_data["total_distance"]
        estimated_time = itinerary_data["estimated_time"]
        # Calcular días reales sumando stay_days
        estimated_days = sum(city.get("days") or city.get("stay_days", 1) for city in cities)
        # Formatear información de ciudades
        cities_info = []
        for i, city in enumerate(cities, 1):
            city_info = f"{i}. {city['name']}"
            if city.get("arrival_dt") and city.get("departure_dt"):
                from datetime import datetime as _dt
                arr = _dt.fromisoformat(city["arrival_dt"]).strftime("%d/%m %H:%M")
                dep = _dt.fromisoformat(city["departure_dt"]).strftime("%d/%m %H:%M")
                stay = ( _dt.fromisoformat(city["departure_dt"]) - _dt.fromisoformat(city["arrival_dt"]) ).days
                city_info += f" (Llegada: {arr}, Salida: {dep}, Estancia: {stay} días)"
            elif city.get("days") or city.get("stay_days"):
                city_info += f" - Estancia: {city.get('days') or city.get('stay_days')} días"
            if city.get("population"):
                city_info += f" (Población: {city['population']:,})"
            if city.get("latitude") and city.get("longitude"):
                city_info += f" - Coord.: {city['latitude']:.4f}, {city['longitude']:.4f}"
            cities_info.append(city_info)
        
        cities_text = "\n".join(cities_info)
        
        prompt = f"""
Crea un itinerario detallado para un viaje a {country}.

INFORMACIÓN DEL VIAJE:
- País: {country}
- Ciudades a visitar: {len(cities)}
- Distancia total: {total_distance:.1f} km
- Tiempo estimado de viaje: {estimated_time:.1f} horas
- Días estimados: {estimated_days} días

CIUDADES:
{cities_text}

RUTA OPTIMIZADA:
- Algoritmo usado: {route.get('algorithm', 'unknown')}
- Ruta sugerida: {' → '.join([city['name'] for city in route.get('cities', cities)])}

REQUERIMIENTOS:
1. Crea un itinerario día por día
2. Incluye actividades específicas para cada ciudad
3. Sugiere lugares de interés, restaurantes y actividades
4. Considera el tiempo de transporte entre ciudades
5. Incluye consejos prácticos de viaje
6. Mantén un tono atractivo y conversacional
7. Considera la cultura y características de {country}

FORMATO:
- Usa un formato claro con días numerados
- Incluye horarios aproximados
- Menciona actividades específicas
- Incluye consejos de transporte
- Sugiere lugares de interés
- Añade consejos culturales y prácticos
"""
        
        return prompt
    
    def create_detailed_itinerary(self, country: str, cities: List[Dict[str, Any]], 
                                 route: Dict[str, Any], preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crea un itinerario más detallado considerando preferencias del usuario.
        """
        try:
            # Agregar preferencias al itinerario
            itinerary_data = {
                "country": country,
                "cities": cities,
                "route": route,
                "preferences": preferences or {},
                "total_distance": route.get("total_distance", 0),
                "estimated_time": route.get("estimated_time", 0)
            }
            
            # Generar itinerario detallado
            detailed_itinerary = self._generate_detailed_itinerary(itinerary_data)
            
            # Crear estructura de respuesta
            response = {
                "itinerary": detailed_itinerary,
                "summary": {
                    "country": country,
                    "total_cities": len(cities),
                    "total_distance_km": route.get("total_distance", 0),
                    "estimated_time_hours": route.get("estimated_time", 0),
                    "preferences_applied": bool(preferences)
                },
                "cities": cities,
                "route_details": route,
                "preferences": preferences
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creando itinerario detallado: {e}")
            return {
                "error": str(e),
                "itinerary": "No se pudo generar el itinerario detallado"
            }
    
    def _generate_detailed_itinerary(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Genera un itinerario más detallado considerando preferencias.
        """
        try:
            # Preparar prompt detallado
            prompt = self._create_detailed_prompt(itinerary_data)
            
            # Llamar a la IA
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en viajes y turismo. Crea itinerarios muy detallados y personalizados.

INSTRUCCIONES:
1. Crea itinerarios día por día con horarios específicos
2. Incluye actividades detalladas para cada ciudad
3. Sugiere lugares específicos con nombres y direcciones
4. Incluye recomendaciones de restaurantes y hoteles
5. Considera las preferencias del usuario
6. Incluye consejos de transporte detallados
7. Añade información cultural y histórica
8. Sugiere actividades alternativas en caso de mal tiempo
9. Incluye presupuesto estimado para actividades
10. Considera la temporada y clima del país

FORMATO:
- Día 1: [Nombre de la ciudad]
  - 09:00 - [Actividad específica]
  - 12:00 - [Restaurante recomendado]
  - 14:00 - [Lugar de interés]
  - 18:00 - [Actividad de tarde]
  - 20:00 - [Cena y actividades nocturnas]
  
- Consejos del día: [Consejos específicos]
- Transporte: [Detalles de transporte]
- Presupuesto estimado: [Cantidad]
"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generando itinerario detallado: {e}")
            return f"No se pudo generar el itinerario detallado: {str(e)}"
    
    def _create_detailed_prompt(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Crea el prompt para el itinerario detallado.
        """
        country = itinerary_data["country"]
        cities = itinerary_data["cities"]
        route = itinerary_data["route"]
        preferences = itinerary_data.get("preferences", {})
        
        # Formatear preferencias
        preferences_text = ""
        if preferences:
            pref_list = []
            for key, value in preferences.items():
                pref_list.append(f"- {key}: {value}")
            preferences_text = "\n".join(pref_list)
        
        # Formatear ciudades con información detallada
        cities_detailed = []
        for i, city in enumerate(cities, 1):
            city_info = f"Día {i}: {city['name']}"
            if city.get("population"):
                city_info += f" (Población: {city['population']:,})"
            if city.get("type"):
                city_info += f" - Tipo: {city['type']}"
            cities_detailed.append(city_info)
        
        cities_text = "\n".join(cities_detailed)
        
        prompt = f"""
Crea un itinerario MUY DETALLADO para un viaje a {country}.

INFORMACIÓN DEL VIAJE:
- País: {country}
- Número de ciudades: {len(cities)}
- Distancia total: {route.get('total_distance', 0):.1f} km
- Tiempo estimado: {route.get('estimated_time', 0):.1f} horas

CIUDADES A VISITAR:
{cities_text}

PREFERENCIAS DEL USUARIO:
{preferences_text if preferences_text else "No se especificaron preferencias"}

RUTA OPTIMIZADA:
- Algoritmo: {route.get('algorithm', 'unknown')}
- Ruta: {' → '.join([city['name'] for city in route.get('cities', cities)])}

REQUERIMIENTOS DETALLADOS:
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
- Día X: [Nombre ciudad]
  - 09:00 - [Actividad específica con detalles]
  - 12:00 - [Restaurante con nombre y tipo de comida]
  - 14:00 - [Lugar de interés con información]
  - 18:00 - [Actividad de tarde]
  - 20:00 - [Cena y actividades nocturnas]
  
- Consejos del día: [Consejos específicos]
- Transporte: [Detalles de transporte]
- Presupuesto estimado: [Cantidad]
- Información cultural: [Datos culturales]
"""
        
        return prompt 