from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models.city import City
import logging

logger = logging.getLogger(__name__)

class CityService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.DATABASE_NAME]
        self.collection = self.db.cities

    async def get_cities_by_country(self, country_code: str) -> List[City]:
        """
        Get all cities for a given country code.
        """
        try:
            cursor = self.collection.find({"country": country_code.upper()})
            cities = await cursor.to_list(length=None)
            return [City(**city) for city in cities]
        except Exception as e:
            logger.error(f"Error getting cities for country {country_code}: {str(e)}")
            return []

    async def get_city_by_name(self, name: str, country_code: Optional[str] = None) -> Optional[City]:
        """
        Get a city by name, optionally filtering by country code.
        """
        try:
            query = {"name": {"$regex": f"^{name}$", "$options": "i"}}
            if country_code:
                query["country"] = country_code.upper()
            
            city = await self.collection.find_one(query)
            return City(**city) if city else None
        except Exception as e:
            logger.error(f"Error getting city {name}: {str(e)}")
            return None

    async def search_cities(self, query: str, country_code: Optional[str] = None) -> List[City]:
        """
        Search cities by name, optionally filtering by country code.
        Uses fuzzy matching for better results.
        """
        try:
            search_query = {
                "name": {"$regex": query, "$options": "i"}
            }
            if country_code:
                search_query["country"] = country_code.upper()

            cursor = self.collection.find(search_query)
            cities = await cursor.to_list(length=None)
            return [City(**city) for city in cities]
        except Exception as e:
            logger.error(f"Error searching cities with query {query}: {str(e)}")
            return []

    async def get_popular_cities(self, country_code: str, limit: int = 5) -> List[City]:
        """
        Get the most populous cities for a given country.
        """
        try:
            cursor = self.collection.find(
                {"country": country_code.upper()}
            ).sort("population", -1).limit(limit)
            
            cities = await cursor.to_list(length=None)
            return [City(**city) for city in cities]
        except Exception as e:
            logger.error(f"Error getting popular cities for country {country_code}: {str(e)}")
            return []

# Create a singleton instance
city_service = CityService() 