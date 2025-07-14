from typing import List, Dict, Any
from openai import AzureOpenAI
from app.config import settings
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AIMatchingService:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    async def match_cities(
        self, 
        ai_suggested_cities: List[str], 
        available_cities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Usa IA para hacer match entre ciudades sugeridas y ciudades disponibles en BD
        """
        try:
            # Preparar datos para la IA
            available_cities_formatted = [
                {
                    "id": str(city["_id"]),
                    "name": city["name"],
                    "country_code": city.get("country_code", ""),
                    "population": city.get("population", 0)
                }
                for city in available_cities
            ]

            # Crear prompt para la IA
            prompt = f"""
            Necesito que hagas match entre las ciudades sugeridas por IA y las ciudades disponibles en mi base de datos.

            CIUDADES SUGERIDAS POR IA:
            {json.dumps(ai_suggested_cities, indent=2)}

            CIUDADES DISPONIBLES EN BASE DE DATOS:
            {json.dumps(available_cities_formatted, indent=2)}

            INSTRUCCIONES:
            1. Para cada ciudad sugerida por IA, encuentra la mejor coincidencia en la base de datos
            2. Considera variaciones de nombres (ej: "Bangkok" puede coincidir con "Bangkok")
            3. Asigna un nivel de confianza (0.0 a 1.0) para cada match
            4. Si no encuentras coincidencia, marca como "unmatched"

            RESPONDE EN FORMATO JSON:
            {{
                "matched_cities": [
                    {{
                        "ai_name": "nombre de la ciudad sugerida",
                        "db_id": "id de la ciudad en BD",
                        "db_name": "nombre exacto en BD",
                        "confidence": 0.95
                    }}
                ],
                "unmatched_cities": [
                    {{
                        "ai_name": "nombre de la ciudad sugerida",
                        "reason": "razón por la que no se encontró match"
                    }}
                ]
            }}
            """

            # Llamar a la IA
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un experto en hacer matching de nombres de ciudades. Responde solo en formato JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Baja temperatura para respuestas más consistentes
            )

            # Procesar respuesta
            response_content = response.choices[0].message.content
            result = json.loads(response_content)

            logger.info(f"AI matching completed: {len(result.get('matched_cities', []))} matched, {len(result.get('unmatched_cities', []))} unmatched")

            return result

        except Exception as e:
            logger.error(f"Error in AI city matching: {str(e)}")
            return {
                "matched_cities": [],
                "unmatched_cities": ai_suggested_cities,
                "error": str(e)
            }

    async def match_cities_with_sites(
        self, 
        ai_suggested_cities: List[str], 
        available_sites: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Usa IA para hacer match entre ciudades sugeridas y sitios disponibles en BD
        """
        try:
            # Preparar datos para la IA con la estructura correcta de sites
            available_sites_formatted = [
                {
                    "id": str(site["_id"]),
                    "name": site["name"],
                    "normalized_name": site.get("normalized_name", ""),
                    "description": site.get("description", ""),
                    "hierarchy": site.get("hierarchy", []),
                    "coordinates": {
                        "lat": site.get("lat", ""),
                        "lon": site.get("lon", "")
                    }
                }
                for site in available_sites
            ]

            # Crear prompt para la IA
            prompt = f"""
            Necesito que hagas match entre las ciudades sugeridas por IA y los sitios disponibles en mi base de datos.

            CIUDADES SUGERIDAS POR IA:
            {json.dumps(ai_suggested_cities, indent=2)}

            SITIOS DISPONIBLES EN BASE DE DATOS (SOLO DEL PAÍS ESPECIFICADO):
            {json.dumps(available_sites_formatted, indent=2)}

            INSTRUCCIONES CRÍTICAS:
            1. SOLO haz match con sitios que estén en la lista de "SITIOS DISPONIBLES"
            2. Para cada ciudad sugerida por IA, encuentra la mejor coincidencia en la base de datos
            3. Considera variaciones de nombres (ej: "Bangkok" puede coincidir con "Bangkok", "Ao Nang" con "Ao Nang")
            4. Usa tanto el nombre normal como el normalized_name para hacer match
            5. Asigna un nivel de confianza (0.0 a 1.0) para cada match
            6. Si no encuentras coincidencia, marca como "unmatched"
            7. NO inventes ciudades que no estén en la lista de disponibles

            RESPONDE EN FORMATO JSON:
            {{
                "matched_cities": [
                    {{
                        "ai_name": "nombre de la ciudad sugerida",
                        "db_id": "id del sitio en BD",
                        "db_name": "nombre exacto en BD",
                        "confidence": 0.95
                    }}
                ],
                "unmatched_cities": [
                    {{
                        "ai_name": "nombre de la ciudad sugerida",
                        "reason": "razón por la que no se encontró match"
                    }}
                ]
            }}
            """

            # Llamar a la IA
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un experto en hacer matching de nombres de ciudades y sitios turísticos. SOLO haz match con sitios que estén en la lista proporcionada. Responde solo en formato JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Baja temperatura para respuestas más consistentes
            )

            # Procesar respuesta
            response_content = response.choices[0].message.content
            result = json.loads(response_content)

            logger.info(f"AI matching with sites completed: {len(result.get('matched_cities', []))} matched, {len(result.get('unmatched_cities', []))} unmatched")

            return result

        except Exception as e:
            logger.error(f"Error in AI city-site matching: {str(e)}")
            return {
                "matched_cities": [],
                "unmatched_cities": ai_suggested_cities,
                "error": str(e)
            }

    async def create_itinerary_from_matches(
        self,
        matched_cities: List[Dict[str, Any]],
        travel_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Crea un itinerario basado en las ciudades que hicieron match
        """
        try:
            # Obtener detalles completos de las ciudades
            from app.database import get_cities_collection
            from bson import ObjectId
            
            cities_collection = await get_cities_collection()
            city_ids = [ObjectId(city["db_id"]) for city in matched_cities]
            
            city_details = await cities_collection.find({
                "_id": {"$in": city_ids}
            }).to_list(length=None)

            # Crear itinerario
            itinerary_data = {
                "travel_id": travel_id,
                "cities": [
                    {
                        "city_id": str(city["_id"]),
                        "name": city["name"],
                        "country_code": city.get("country_code", ""),
                        "population": city.get("population", 0),
                        "coordinates": city.get("coordinates", {}),
                        "ai_confidence": next(
                            (match["confidence"] for match in matched_cities 
                             if match["db_id"] == str(city["_id"])), 
                            0.0
                        )
                    }
                    for city in city_details
                ],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Guardar en BD
            from app.crud import travel as travel_crud
            from app.models.travel import ItineraryCreate
            
            itinerary = await travel_crud.create_or_update_itinerary(
                ItineraryCreate(**itinerary_data)
            )

            return {
                "itinerary": itinerary,
                "matched_count": len(matched_cities),
                "total_cities": len(city_details)
            }

        except Exception as e:
            logger.error(f"Error creating itinerary from matches: {str(e)}")
            raise

    async def create_itinerary_from_sites(
        self,
        matched_cities: List[Dict[str, Any]],
        travel_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Crea un itinerario basado en los sitios que hicieron match
        """
        try:
            # Obtener detalles completos de los sitios
            from app.database import get_sites_collection
            from bson import ObjectId
            
            sites_collection = await get_sites_collection()
            site_ids = [ObjectId(city["db_id"]) for city in matched_cities]
            
            site_details = await sites_collection.find({
                "_id": {"$in": site_ids}
            }).to_list(length=None)

            # Crear itinerario
            itinerary_data = {
                "travel_id": travel_id,
                "cities": [
                    {
                        "site_id": str(site["_id"]),
                        "name": site["name"],
                        "normalized_name": site.get("normalized_name", ""),
                        "description": site.get("description", ""),
                        "coordinates": {
                            "latitude": float(site.get("lat", 0)),
                            "longitude": float(site.get("lon", 0))
                        }
                    }
                    for site in site_details
                ],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Guardar en BD
            from app.crud import travel as travel_crud
            from app.models.travel import ItineraryCreate
            
            itinerary = await travel_crud.create_or_update_itinerary(
                ItineraryCreate(**itinerary_data)
            )

            return {
                "itinerary": itinerary,
                "matched_count": len(matched_cities),
                "total_sites": len(site_details)
            }

        except Exception as e:
            logger.error(f"Error creating itinerary from sites: {str(e)}")
            raise

# Instancia global del servicio
ai_matching_service = AIMatchingService() 