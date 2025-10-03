"""
Agent specialized in generating detailed itineraries using AI.
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
    Agent specialized in generating detailed itineraries.
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
        Creates a detailed itinerary based on country, cities and route.
        """
        try:
            # Prepare data for AI
            itinerary_data = {
                "country": country,
                "cities": cities,
                "route": route,
                "total_distance": route.get("total_distance", 0),
                "estimated_time": route.get("estimated_time", 0),
                "algorithm": route.get("algorithm", "unknown")
            }
            
            # Generate itinerary using AI
            itinerary = self._generate_itinerary_with_ai(itinerary_data)
            
            # Create response structure
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
            self.logger.error(f"Error creating itinerary: {e}")
            return {
                "error": str(e),
                "itinerary": "Could not generate the itinerary",
                "summary": {
                    "country": country,
                    "total_cities": len(cities),
                    "error": True
                }
            }
    
    def _generate_itinerary_with_ai(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Generates the itinerary using AI.
        """
        try:
            # Prepare prompt for AI
            prompt = self._create_itinerary_prompt(itinerary_data)
            
            # Call AI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a travel and tourism expert. Your task is to create detailed and attractive itineraries.

INSTRUCTIONS:
1. Create realistic and practical itineraries
2. Include specific activities for each city
3. Consider travel time between cities
4. Suggest places of interest, restaurants and activities
5. Maintain a conversational and attractive tone
6. Include practical travel tips
7. Consider the culture and characteristics of the country

RESPONSE FORMAT:
- Use a clear and structured format
- Include numbered days
- Mention specific activities
- Include transportation tips
- Suggest places of interest
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
            self.logger.error(f"Error generating itinerary with AI: {e}")
            return f"Could not generate the itinerary: {str(e)}"
    
    def _create_itinerary_prompt(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Creates the prompt to generate the itinerary.
        """
        country = itinerary_data["country"]
        cities = itinerary_data["cities"]
        route = itinerary_data["route"]
        total_distance = itinerary_data["total_distance"]
        estimated_time = itinerary_data["estimated_time"]
        # Calculate real days by summing stay_days
        estimated_days = sum(city.get("days") or city.get("stay_days", 1) for city in cities)
        # Format city information
        cities_info = []
        for i, city in enumerate(cities, 1):
            city_info = f"{i}. {city['name']}"
            if city.get("arrival_dt") and city.get("departure_dt"):
                from datetime import datetime as _dt
                arr = _dt.fromisoformat(city["arrival_dt"]).strftime("%d/%m %H:%M")
                dep = _dt.fromisoformat(city["departure_dt"]).strftime("%d/%m %H:%M")
                stay = ( _dt.fromisoformat(city["departure_dt"]) - _dt.fromisoformat(city["arrival_dt"]) ).days
                city_info += f" (Arrival: {arr}, Departure: {dep}, Stay: {stay} days)"
            elif city.get("days") or city.get("stay_days"):
                city_info += f" - Stay: {city.get('days') or city.get('stay_days')} days"
            if city.get("population"):
                city_info += f" (Population: {city['population']:,})"
            if city.get("latitude") and city.get("longitude"):
                city_info += f" - Coords.: {city['latitude']:.4f}, {city['longitude']:.4f}"
            cities_info.append(city_info)
        
        cities_text = "\n".join(cities_info)
        
        prompt = f"""
Create a detailed itinerary for a trip to {country}.

TRIP INFORMATION:
- Country: {country}
- Cities to visit: {len(cities)}
- Total distance: {total_distance:.1f} km
- Estimated travel time: {estimated_time:.1f} hours
- Estimated days: {estimated_days} days

CITIES:
{cities_text}

OPTIMIZED ROUTE:
- Algorithm used: {route.get('algorithm', 'unknown')}
- Suggested route: {' → '.join([city['name'] for city in route.get('cities', cities)])}

REQUIREMENTS:
1. Create a day-by-day itinerary
2. Include specific activities for each city
3. Suggest places of interest, restaurants and activities
4. Consider transportation time between cities
5. Include practical travel tips
6. Maintain an attractive and conversational tone
7. Consider the culture and characteristics of {country}

FORMAT:
- Use a clear format with numbered days
- Include approximate schedules
- Mention specific activities
- Include transportation tips
- Suggest places of interest
- Add cultural and practical tips
"""
        
        return prompt
    
    def create_detailed_itinerary(self, country: str, cities: List[Dict[str, Any]], 
                                 route: Dict[str, Any], preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Creates a more detailed itinerary considering user preferences.
        """
        try:
            # Add preferences to itinerary
            itinerary_data = {
                "country": country,
                "cities": cities,
                "route": route,
                "preferences": preferences or {},
                "total_distance": route.get("total_distance", 0),
                "estimated_time": route.get("estimated_time", 0)
            }
            
            # Generate detailed itinerary
            detailed_itinerary = self._generate_detailed_itinerary(itinerary_data)
            
            # Create response structure
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
            self.logger.error(f"Error creating detailed itinerary: {e}")
            return {
                "error": str(e),
                "itinerary": "Could not generate the detailed itinerary"
            }
    
    def _generate_detailed_itinerary(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Generates a more detailed itinerary considering preferences.
        """
        try:
            # Prepare detailed prompt
            prompt = self._create_detailed_prompt(itinerary_data)
            
            # Call AI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a travel and tourism expert. Create very detailed and personalized itineraries.

INSTRUCTIONS:
1. Create day-by-day itineraries with specific schedules
2. Include detailed activities for each city
3. Suggest specific places with names and addresses
4. Include restaurant and hotel recommendations
5. Consider user preferences
6. Include detailed transportation tips
7. Add cultural and historical information
8. Suggest alternative activities in case of bad weather
9. Include estimated budget for activities
10. Consider the season and climate of the country

FORMAT:
- Day 1: [City name]
  - 09:00 - [Specific activity]
  - 12:00 - [Recommended restaurant]
  - 14:00 - [Place of interest]
  - 18:00 - [Afternoon activity]
  - 20:00 - [Dinner and night activities]
  
- Day tips: [Specific tips]
- Transportation: [Transportation details]
- Estimated budget: [Amount]
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
            self.logger.error(f"Error generating detailed itinerary: {e}")
            return f"Could not generate the detailed itinerary: {str(e)}"
    
    def _create_detailed_prompt(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Creates the prompt for the detailed itinerary.
        """
        country = itinerary_data["country"]
        cities = itinerary_data["cities"]
        route = itinerary_data["route"]
        preferences = itinerary_data.get("preferences", {})
        
        # Format preferences
        preferences_text = ""
        if preferences:
            pref_list = []
            for key, value in preferences.items():
                pref_list.append(f"- {key}: {value}")
            preferences_text = "\n".join(pref_list)
        
        # Format cities with detailed information
        cities_detailed = []
        for i, city in enumerate(cities, 1):
            city_info = f"Day {i}: {city['name']}"
            if city.get("population"):
                city_info += f" (Population: {city['population']:,})"
            if city.get("type"):
                city_info += f" - Type: {city['type']}"
            cities_detailed.append(city_info)
        
        cities_text = "\n".join(cities_detailed)
        
        prompt = f"""
Create a VERY DETAILED itinerary for a trip to {country}.

TRIP INFORMATION:
- Country: {country}
- Number of cities: {len(cities)}
- Total distance: {route.get('total_distance', 0):.1f} km
- Estimated time: {route.get('estimated_time', 0):.1f} hours

CITIES TO VISIT:
{cities_text}

USER PREFERENCES:
{preferences_text if preferences_text else "No preferences specified"}

OPTIMIZED ROUTE:
- Algorithm: {route.get('algorithm', 'unknown')}
- Route: {' → '.join([city['name'] for city in route.get('cities', cities)])}

DETAILED REQUIREMENTS:
1. Create a day-by-day itinerary with specific schedules
2. Include detailed activities for each city
3. Suggest specific places with names and addresses
4. Include restaurant and hotel recommendations
5. Consider user preferences
6. Include detailed transportation tips
7. Add cultural and historical information
8. Suggest alternative activities
9. Include estimated budget
10. Consider climate and season

SPECIFIC FORMAT:
- Day X: [City name]
  - 09:00 - [Specific activity with details]
  - 12:00 - [Restaurant with name and food type]
  - 14:00 - [Place of interest with information]
  - 18:00 - [Afternoon activity]
  - 20:00 - [Dinner and night activities]
  
- Day tips: [Specific tips]
- Transportation: [Transportation details]
- Estimated budget: [Amount]
- Cultural information: [Cultural data]
"""
        
        return prompt 