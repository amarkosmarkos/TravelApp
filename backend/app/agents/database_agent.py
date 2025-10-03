"""
Agent specialized in MongoDB database queries.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_sites_collection, get_cities_collection
import logging
import json

logger = logging.getLogger(__name__)

class DatabaseAgent:
    """
    Agent specialized in MongoDB database queries.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def search_cities_by_country(self, country_name: str) -> List[Dict[str, Any]]:
        """
        Searches for cities in the database by country (only sites with subtype city).
        """
        try:
            # Normalize country name
            country_name = country_name.lower().strip()
            
            # Country to ISO code mapping
            country_mapping = {
                "thailand": "TH",
                "japan": "JP", 
                "spain": "ES",
                "france": "FR",
                "italy": "IT",
                "germany": "DE",
                "united kingdom": "GB",
                "uk": "GB",
                "england": "GB",
                "usa": "US",
                "united states": "US",
                "america": "US",
                "china": "CN",
                "south korea": "KR",
                "korea": "KR",
                "australia": "AU",
                "canada": "CA",
                "brazil": "BR",
                "argentina": "AR",
                "mexico": "MX",
                "peru": "PE",
                "chile": "CL",
                "colombia": "CO",
                "venezuela": "VE",
                "ecuador": "EC",
                "bolivia": "BO",
                "paraguay": "PY",
                "uruguay": "UY",
                "guyana": "GY",
                "suriname": "SR",
                "french guiana": "GF"
            }
            
            country_code = country_mapping.get(country_name)
            if not country_code:
                self.logger.warning(f"Country code not found for: {country_name}")
                return []
            
            # Search only in sites collection with subtype city
            sites_collection = await get_sites_collection()
            sites = await sites_collection.find(
                {
                    "hierarchy": {"$elemMatch": {"type": "country", "code": country_code}},
                    "subtype": "city"
                },
                {
                    "_id": 1,
                    "name": 1,
                    "subtype": 1,
                    "description": 1,
                    "lat": 1,
                    "lon": 1,
                    "type": 1,
                    "hierarchy": 1
                }
            ).to_list(length=None)
            
            # Formatear resultados
            results = []
            for site in sites:
                results.append({
                    "id": str(site["_id"]),
                    "name": site["name"],
                    "type": "city",
                    "description": site.get("description", ""),
                    "country_code": country_code,
                    "latitude": float(site.get("lat", 0)) if site.get("lat") else None,
                    "longitude": float(site.get("lon", 0)) if site.get("lon") else None,
                    "source": "sites"
                })
            
            self.logger.info(f"Encontradas {len(results)} ciudades para {country_name} ({country_code})")
            return results
            
        except Exception as e:
            self.logger.error(f"Error buscando ciudades para {country_name}: {e}")
            return []
    
    async def search_sites_by_city(self, city_name: str, country_code: str = None) -> List[Dict[str, Any]]:
        """
        Busca sitios específicos en una ciudad.
        """
        try:
            sites_collection = await get_sites_collection()
            
            # Construir filtro
            filter_query = {"city": {"$regex": city_name, "$options": "i"}}
            if country_code:
                filter_query["country_code"] = country_code
            
            sites = await sites_collection.find(
                filter_query,
                {
                    "_id": 1,
                    "name": 1,
                    "city": 1,
                    "country_code": 1,
                    "latitude": 1,
                    "longitude": 1,
                    "type": 1,
                    "description": 1
                }
            ).to_list(length=None)
            
            results = []
            for site in sites:
                results.append({
                    "id": str(site["_id"]),
                    "name": site["name"],
                    "city": site["city"],
                    "country_code": site["country_code"],
                    "latitude": site.get("latitude"),
                    "longitude": site.get("longitude"),
                    "type": site.get("type"),
                    "description": site.get("description", "")
                })
            
            self.logger.info(f"Encontrados {len(results)} sitios para {city_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error buscando sitios para {city_name}: {e}")
            return []

    async def search_sites_by_parent_or_city_id(self, city_site_id: str) -> List[Dict[str, Any]]:
        """
        Devuelve sitios (POIs) relacionados con una ciudad identificada por su site_id/city_id.
        Intenta por jerarquía (elemMatch id), city_id o parent_id.
        """
        try:
            sites_collection = await get_sites_collection()
            query = {
                "$or": [
                    {"city_id": city_site_id},
                    {"parent_id": city_site_id},
                    {"hierarchy": {"$elemMatch": {"id": city_site_id}}}
                ]
            }
            fields = {
                "_id": 1, "name": 1, "type": 1, "subtype": 1,
                "latitude": 1, "longitude": 1, "lat": 1, "lon": 1
            }
            docs = await sites_collection.find(query, fields).limit(500).to_list(length=None)
            results: List[Dict[str, Any]] = []
            for d in docs:
                results.append({
                    "id": str(d.get("_id")),
                    "name": d.get("name"),
                    "type": d.get("type") or d.get("subtype"),
                    "latitude": d.get("latitude") or d.get("lat"),
                    "longitude": d.get("longitude") or d.get("lon"),
                })
            return results
        except Exception as e:
            self.logger.error(f"search_sites_by_parent_or_city_id error: {e}")
            return []

    async def search_sites_near_coords(self, lat: float, lon: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Busca sitios cerca de unas coordenadas. Si no hay índices geoespaciales, usa bounding box aproximada.
        """
        try:
            sites_collection = await get_sites_collection()
            # Bounding box aproximado
            delta_lat = radius_km / 111.0
            import math
            delta_lon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.2))

            numeric_query = {
                "latitude": {"$gte": lat - delta_lat, "$lte": lat + delta_lat},
                "longitude": {"$gte": lon - delta_lon, "$lte": lon + delta_lon}
            }
            string_query = {
                "lat": {"$exists": True, "$ne": None},
                "lon": {"$exists": True, "$ne": None}
            }
            fields = {
                "_id": 1, "name": 1, "type": 1, "subtype": 1,
                "latitude": 1, "longitude": 1, "lat": 1, "lon": 1
            }

            numeric_docs = await sites_collection.find(numeric_query, fields).limit(300).to_list(length=None)
            string_docs = await sites_collection.find(string_query, fields).limit(300).to_list(length=None)

            results: List[Dict[str, Any]] = []

            def _push(doc: Dict[str, Any]):
                results.append({
                    "id": str(doc.get("_id")),
                    "name": doc.get("name"),
                    "type": doc.get("type") or doc.get("subtype"),
                    "latitude": doc.get("latitude") or doc.get("lat"),
                    "longitude": doc.get("longitude") or doc.get("lon"),
                })

            for d in numeric_docs:
                _push(d)

            for d in string_docs:
                try:
                    lat_f = float(d.get("lat"))
                    lon_f = float(d.get("lon"))
                    if (lat - delta_lat) <= lat_f <= (lat + delta_lat) and (lon - delta_lon) <= lon_f <= (lon + delta_lon):
                        _push(d)
                except Exception:
                    continue

            # Limitar resultados para evitar respuestas enormes
            return results[:400]
        except Exception as e:
            self.logger.error(f"search_sites_near_coords error: {e}")
            return []
    
    async def get_city_coordinates(self, city_name: str, country_code: str = None) -> Optional[Dict[str, float]]:
        """
        Obtiene las coordenadas de una ciudad específica.
        """
        try:
            cities_collection = await get_cities_collection()
            
            # Construir filtro
            filter_query = {"name": {"$regex": city_name, "$options": "i"}}
            if country_code:
                filter_query["country_code"] = country_code
            
            city = await cities_collection.find_one(filter_query)
            
            if city and city.get("latitude") and city.get("longitude"):
                return {
                    "latitude": city["latitude"],
                    "longitude": city["longitude"]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo coordenadas para {city_name}: {e}")
            return None
    
    async def get_popular_cities(self, country_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las ciudades más populares de un país basándose en población.
        """
        try:
            cities_collection = await get_cities_collection()
            
            cities = await cities_collection.find(
                {"country_code": country_code},
                {
                    "_id": 1,
                    "name": 1,
                    "country_code": 1,
                    "latitude": 1,
                    "longitude": 1,
                    "population": 1
                }
            ).sort("population", -1).limit(limit).to_list(length=None)
            
            results = []
            for city in cities:
                results.append({
                    "id": str(city["_id"]),
                    "name": city["name"],
                    "country_code": city["country_code"],
                    "latitude": city.get("latitude"),
                    "longitude": city.get("longitude"),
                    "population": city.get("population", 0)
                })
            
            self.logger.info(f"Encontradas {len(results)} ciudades populares para {country_code}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ciudades populares para {country_code}: {e}")
            return [] 