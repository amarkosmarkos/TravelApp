"""
Agente especializado en seleccionar destinos inteligentemente usando IA.
"""

from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from app.config import settings
from app.services.travel_time_service import travel_time_service
import logging
import json
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class DestinationSelectionAgent:
    """
    Agente que usa IA para seleccionar destinos óptimos.
    """
    
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    
    async def select_destinations(
        self, 
        country: str, 
        total_days: int, 
        available_sites: List[Dict[str, Any]],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        IA selecciona destinos basándose en relevancia turística.
        """
        try:
            # Preparar datos para la IA
            sites_formatted = [
                {
                    "name": site["name"],
                    "type": site.get("type", ""),
                    "entity_type": site.get("entity_type", ""),
                    "subtype": site.get("subtype", ""),
                    "description": site.get("description", ""),
                    "coordinates": {
                        "latitude": float(site.get("lat", 0)) if site.get("lat") else 0,
                        "longitude": float(site.get("lon", 0)) if site.get("lon") else 0
                    }
                }
                for site in available_sites
            ]
            
            # Crear prompt para la IA
            prompt = self._create_selection_prompt(
                country, total_days, sites_formatted, user_preferences
            )
            
            # Llamar a la IA (forzar salida JSON)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system", 
                        "content": """Eres un experto en planificación de viajes. Tu tarea es seleccionar los mejores destinos para un viaje.

INSTRUCCIONES:
1. Analiza la importancia turística de cada destino
2. Considera las distancias entre ciudades
3. Selecciona destinos que ofrezcan variedad de experiencias
4. Asigna un score de relevancia (1-10) a cada destino
5. Considera el número total de días disponibles

RESPONDE SOLO EN JSON VÁLIDO (sin texto adicional).
FORMATO:
{
    "selected_cities": [
        {
            "name": "nombre de la ciudad",
            "score": 1.0,
            "reason": "razón"
        }
    ],
    "total_cities": 0
}"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            # Modelos de validación Pydantic
            class SelectedCity(BaseModel):
                name: str
                score: float
                reason: Optional[str] = ""

            class SelectionResult(BaseModel):
                selected_cities: List[SelectedCity]
                total_cities: int

            # Procesar respuesta con tolerancia a ```json
            response_content = response.choices[0].message.content or ""
            try:
                result_raw = json.loads(response_content)
            except Exception:
                import re
                cleaned = re.sub(r"```[a-zA-Z]*", "", response_content).replace("```", "").strip()
                result_raw = json.loads(cleaned)

            try:
                validated = SelectionResult(**result_raw)
            except ValidationError as ve:
                logger.error(f"Selección inválida: {ve}")
                raise
            
            # Validar y optimizar la selección
            optimized_selection = await self._optimize_selection(
                validated.dict(), available_sites, total_days
            )
            
            logger.info(f"IA seleccionó {len(optimized_selection['selected_cities'])} destinos")
            
            return optimized_selection
            
        except Exception as e:
            logger.error(f"Error en selección de destinos: {e}")
            return {
                "selected_cities": [],
                "total_exploration_days": 0,
                "estimated_transport_days": 0,
                "error": str(e)
            }
    
    def _create_selection_prompt(
        self, 
        country: str, 
        total_days: int, 
        sites: List[Dict[str, Any]], 
        preferences: Dict[str, Any] = None
    ) -> str:
        """
        Crea el prompt para la IA.
        """
        preferences_text = ""
        if preferences:
            preferences_text = f"\nPREFERENCIAS DEL USUARIO:\n{json.dumps(preferences, indent=2)}"
        
        return f"""
        Selecciona los mejores destinos para un viaje a {country} de {total_days} días.

        DESTINOS DISPONIBLES:
        {json.dumps(sites, indent=2)}

        {preferences_text}

        CONSIDERACIONES:
        - Días totales: {total_days}
        - Días de exploración disponibles: {total_days - 1} (1 día para llegada/salida)
        - Considera tiempo de transporte entre ciudades
        - Prioriza destinos con mayor valor turístico
        - Busca variedad de experiencias (cultura, naturaleza, playas, etc.)
        - No sobrecargues el itinerario

        Selecciona los destinos más apropiados y asigna días de manera inteligente.
        """
    
    async def _optimize_selection(
        self, 
        ai_selection: Dict[str, Any], 
        available_sites: List[Dict[str, Any]], 
        total_days: int
    ) -> Dict[str, Any]:
        """
        Optimiza la selección de la IA basándose en relevancia turística.
        """
        try:
            selected_cities = ai_selection.get("selected_cities", [])
            
            if not selected_cities:
                return ai_selection
            
            # Convertir nombres de ciudades a objetos completos (site + campos IA)
            cities_with_data = []
            for city_info in selected_cities:
                city_name = city_info["name"]
                # Buscar el site correspondiente
                for site in available_sites:
                    if site["name"].lower() == city_name.lower():
                        site_obj = site.copy()  # Copia todos los campos del site
                        # Añadir solo los campos de IA
                        site_obj["score"] = city_info["score"]
                        if "reason" in city_info:
                            site_obj["reason"] = city_info["reason"]
                        cities_with_data.append(site_obj)
                        break
            
            # Ordenar por score de relevancia
            cities_with_data.sort(key=lambda x: x.get("score", 1), reverse=True)
            
            # Limitar a un número razonable de ciudades (máximo 8)
            max_cities = min(8, len(cities_with_data))
            cities_with_data = cities_with_data[:max_cities]
            
            logger.info(f"Ciudades seleccionadas por relevancia: {[c['name'] for c in cities_with_data]}")
            
            return {
                "selected_cities": cities_with_data,
                "total_cities": len(cities_with_data),
                "total_days": total_days
            }
        except Exception as e:
            logger.error(f"Error optimizando selección: {e}")
            return ai_selection

# Instancia global
destination_selection_agent = DestinationSelectionAgent() 