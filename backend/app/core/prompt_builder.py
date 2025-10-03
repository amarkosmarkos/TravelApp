"""
Unified builder for itinerary prompts based on TravelPlan.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
from .scheduler import TravelPlan, CityVisit

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Unified prompt constructor for itineraries.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_itinerary_prompt(self, plan: TravelPlan, country: str) -> str:
        """
        Builds prompt to generate detailed itinerary.
        """
        try:
            # Format city information with times
            cities_info = self._format_cities_with_times(plan.visits)
            
            # Calculate statistics
            total_days = (plan.end_dt - plan.start_dt).days
            total_cities = len(plan.visits)
            
            prompt = f"""
Create a detailed itinerary for a trip to {country}.

TRAVEL INFORMATION:
- Country: {country}
- Start date: {plan.start_dt.strftime('%d/%m/%Y %H:%M')}
- End date: {plan.end_dt.strftime('%d/%m/%Y %H:%M')}
- Total duration: {total_days} days
- Cities to visit: {total_cities}
- Exploration hours: {plan.total_explore_hours:.1f}h
- Travel hours: {plan.total_travel_hours:.1f}h

CITIES WITH SCHEDULES:
{cities_info}

USER PREFERENCES:
{self._format_preferences(plan.preferences)}

REQUIREMENTS:
1. Create a day-by-day itinerary with specific times
2. Include detailed activities for each city
3. Suggest specific places with names and addresses
4. Include restaurant and hotel recommendations
5. Consider user preferences
6. Include detailed transportation advice
7. Add cultural and historical information
8. Suggest alternative activities
9. Include estimated budget
10. Consider climate and season

SPECIFIC FORMAT:
- Day X: [City name] - [Arrival date] to [Departure date]
  - [Arrival time] - [Specific activity with details]
  - [Lunch time] - [Restaurant with name and food type]
  - [Afternoon time] - [Place of interest with information]
  - [Evening time] - [Dinner and night activities]
  
- Transportation: [Transportation details to next city]
- Day tips: [Specific tips]
- Estimated budget: [Amount]
- Cultural information: [Cultural data]
"""
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error building prompt: {e}")
            return self._build_fallback_prompt(country, plan.visits)
    
    def build_modification_prompt(self, plan: TravelPlan, user_request: str) -> str:
        """
        Builds prompt to analyze modifications.
        """
        try:
            current_cities = self._format_cities_for_modification(plan.visits)
            
            prompt = f"""
Analyze the user's modification request and suggest changes to the itinerary.

USER REQUEST: "{user_request}"

CURRENT ITINERARY:
{current_cities}

INSTRUCTIONS:
1. Understand the user's intention (change, add, remove cities)
2. Identify the mentioned cities
3. Suggest appropriate changes
4. Maintain itinerary coherence
5. Consider distances and travel time

RESPOND IN JSON FORMAT:
{{
    "intention": "modification type (change, add, remove, optimize)",
    "changes": [
        {{
            "action": "add/remove/replace",
            "city_name": "city name",
            "reason": "change reason"
        }}
    ],
    "modified_cities": [
        {{
            "name": "city name",
            "score": relevance number (1-10),
            "type": "site type",
            "description": "description"
        }}
    ],
    "message": "explanatory message of changes"
}}
"""
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error building modification prompt: {e}")
            return ""
    
    def _format_cities_with_times(self, visits: List[CityVisit]) -> str:
        """
        Formats cities with time information.
        """
        cities_info = []
        
        for i, visit in enumerate(visits, 1):
            # Calculate stay days
            stay_days = visit.stay_hours / 24
            
            # Format dates
            arrival_str = visit.arrival_dt.strftime("%d/%m %H:%M")
            departure_str = visit.departure_dt.strftime("%d/%m %H:%M")
            
            city_info = f"{i}. {visit.name}"
            city_info += f" (Arrival: {arrival_str}, Departure: {departure_str}, Stay: {stay_days:.1f} days)"
            
            # Add additional information
            if visit.metadata.get("population"):
                city_info += f" (Population: {visit.metadata['population']:,})"
            
            if visit.metadata.get("type"):
                city_info += f" - Type: {visit.metadata['type']}"
            
            if visit.metadata.get("description"):
                city_info += f" - {visit.metadata['description']}"
            
            # Add transportation to next city
            if visit.transport_hours_from_prev > 0:
                city_info += f" - Transportation from previous: {visit.transport_hours_from_prev:.1f}h"
            
            cities_info.append(city_info)
        
        return "\n".join(cities_info)
    
    def _format_cities_for_modification(self, visits: List[CityVisit]) -> str:
        """
        Formats cities for modification analysis.
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
        Formats user preferences.
        """
        if not preferences:
            return "No preferences specified"
        
        pref_list = []
        for key, value in preferences.items():
            pref_list.append(f"- {key}: {value}")
        
        return "\n".join(pref_list)
    
    def _build_fallback_prompt(self, country: str, visits: List[CityVisit]) -> str:
        """
        Fallback prompt if there's an error in the main one.
        """
        cities_text = "\n".join([f"- {visit.name}" for visit in visits])
        
        return f"""
Create an itinerary for a trip to {country}.

CITIES TO VISIT:
{cities_text}

Create a day-by-day itinerary with specific activities for each city.
""" 