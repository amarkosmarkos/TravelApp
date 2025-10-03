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
        Uses AI to match between suggested cities and available cities in the database
        """
        try:
            # Prepare data for AI
            available_cities_formatted = [
                {
                    "id": str(city["_id"]),
                    "name": city["name"],
                    "country_code": city.get("country_code", ""),
                    "population": city.get("population", 0)
                }
                for city in available_cities
            ]

            # Create prompt for AI
            prompt = f"""
            I need you to match between AI-suggested cities and cities available in my database.

            AI-SUGGESTED CITIES:
            {json.dumps(ai_suggested_cities, indent=2)}

            CITIES AVAILABLE IN DATABASE:
            {json.dumps(available_cities_formatted, indent=2)}

            INSTRUCTIONS:
            1. For each AI-suggested city, find the best match in the database
            2. Consider name variations (e.g., "Bangkok" can match "Bangkok")
            3. Assign a confidence level (0.0 to 1.0) for each match
            4. If no match is found, mark as "unmatched"

            RESPOND IN JSON FORMAT:
            {{
                "matched_cities": [
                    {{
                        "ai_name": "suggested city name",
                        "db_id": "city id in database",
                        "db_name": "exact name in database",
                        "confidence": 0.95
                    }}
                ],
                "unmatched_cities": [
                    {{
                        "ai_name": "suggested city name",
                        "reason": "reason why no match was found"
                    }}
                ]
            }}
            """

            # Call AI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert in city name matching. Respond only in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for more consistent responses
            )

            # Process response
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
        Uses AI to match between suggested cities and available sites in the database
        """
        try:
            # Prepare data for AI with correct sites structure
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

            # Create prompt for AI
            prompt = f"""
            I need you to match between AI-suggested cities and sites available in my database.

            AI-SUGGESTED CITIES:
            {json.dumps(ai_suggested_cities, indent=2)}

            SITES AVAILABLE IN DATABASE (ONLY FROM SPECIFIED COUNTRY):
            {json.dumps(available_sites_formatted, indent=2)}

            CRITICAL INSTRUCTIONS:
            1. ONLY match with sites that are in the "AVAILABLE SITES" list
            2. For each AI-suggested city, find the best match in the database
            3. Consider name variations (e.g., "Bangkok" can match "Bangkok", "Ao Nang" with "Ao Nang")
            4. Use both normal name and normalized_name for matching
            5. Assign a confidence level (0.0 to 1.0) for each match
            6. If no match is found, mark as "unmatched"
            7. DO NOT invent cities that are not in the available list

            RESPOND IN JSON FORMAT:
            {{
                "matched_cities": [
                    {{
                        "ai_name": "suggested city name",
                        "db_id": "site id in database",
                        "db_name": "exact name in database",
                        "confidence": 0.95
                    }}
                ],
                "unmatched_cities": [
                    {{
                        "ai_name": "suggested city name",
                        "reason": "reason why no match was found"
                    }}
                ]
            }}
            """

            # Call AI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert in city and tourist site name matching. ONLY match with sites that are in the provided list. Respond only in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for more consistent responses
            )

            # Process response
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
        Creates an itinerary based on cities that matched
        """
        try:
            # Get complete city details
            from app.database import get_cities_collection
            from bson import ObjectId
            
            cities_collection = await get_cities_collection()
            city_ids = [ObjectId(city["db_id"]) for city in matched_cities]
            
            city_details = await cities_collection.find({
                "_id": {"$in": city_ids}
            }).to_list(length=None)

            # Create itinerary
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

            # Save to database
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
        Creates an itinerary based on sites that matched
        """
        try:
            # Get complete site details
            from app.database import get_sites_collection
            from bson import ObjectId
            
            sites_collection = await get_sites_collection()
            site_ids = [ObjectId(city["db_id"]) for city in matched_cities]
            
            site_details = await sites_collection.find({
                "_id": {"$in": site_ids}
            }).to_list(length=None)

            # Create itinerary with corrected coordinates
            itinerary_data = {
                "travel_id": travel_id,
                "cities": [
                    {
                        "site_id": str(site["_id"]),
                        "name": site["name"],
                        "normalized_name": site.get("normalized_name", ""),
                        "description": site.get("description", ""),
                        # Convert coordinates from string to float
                        "latitude": float(site.get("lat", "0")) if site.get("lat") else None,
                        "longitude": float(site.get("lon", "0")) if site.get("lon") else None,
                        "coordinates": {
                            "latitude": float(site.get("lat", "0")) if site.get("lat") else None,
                            "longitude": float(site.get("lon", "0")) if site.get("lon") else None
                        } if site.get("lat") and site.get("lon") else None,
                        # Additional site information
                        "type": site.get("type", ""),
                        "entity_type": site.get("entity_type", ""),
                        "subtype": site.get("subtype", ""),
                        "wikidata_id": site.get("wikidata_id", ""),
                        "hierarchy": site.get("hierarchy", [])
                    }
                    for site in site_details
                ],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Save to database
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

# Global instance of the service
ai_matching_service = AIMatchingService() 