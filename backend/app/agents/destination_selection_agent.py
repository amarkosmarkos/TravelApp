"""
Agent specialized in intelligently selecting destinations using AI.
"""

from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from app.config import settings
from app.services.travel_time_service import travel_time_service
from app.agents.database_agent import DatabaseAgent
import logging
import json
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class DestinationSelectionAgent:
    """
    Agent that uses AI to select optimal destinations.
    """
    
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.db_agent = DatabaseAgent()
    
    async def select_destinations(
        self, 
        country: str, 
        total_days: int, 
        available_sites: Optional[List[Dict[str, Any]]] = None,
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        AI selects destinations based on tourist relevance.
        """
        try:
            # Load sites if not provided
            if available_sites is None:
                available_sites = await self.db_agent.search_cities_by_country(country)

            # Prepare data for AI (including stringified ID)
            sites_formatted = [
                {
                    "id": str(site.get("_id") or site.get("id") or site.get("site_id") or ""),
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
            
            # Create prompt for AI
            prompt = self._create_selection_prompt(
                country, total_days, sites_formatted, user_preferences
            )
            
            # Call AI (force JSON output)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a travel planning expert. Your task is to select the best destinations for a trip.

INSTRUCTIONS:
1. Analyze the tourist importance of each destination
2. Consider distances between cities
3. Select destinations that offer variety of experiences
4. Assign a relevance score (1-10) to each destination
5. Consider the total number of available days
6. ALWAYS return the exact "id" identifier of each destination as it appears in the provided list. Do not invent or translate names.
7. The reason should be brief (max. 15-20 words) for each destination.

RESPOND ONLY IN VALID JSON (no additional text).
FORMAT:
{
    "selected_cities": [
        {
            "id": "exact destination id",
            "name": "city name",
            "score": 1.0,
            "reason": "reason"
        }
    ],
    "total_cities": 0
}"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )

            # Pydantic validation models
            class SelectedCity(BaseModel):
                id: Optional[str] = None
                name: Optional[str] = None
                score: float
                reason: Optional[str] = ""

            class SelectionResult(BaseModel):
                selected_cities: List[SelectedCity]
                total_cities: int

            # Process response with tolerance to ```json
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
                logger.error(f"Invalid selection: {ve}")
                raise
            
            # Debug: how many elements the LLM returned before mapping
            try:
                llm_items = result_raw.get("selected_cities", [])
                logger.info(f"LLM returned {len(llm_items)} cities (before id/name mapping)")
            except Exception:
                pass

            # Validate and optimize the selection
            optimized_selection = await self._optimize_selection(
                validated.dict(), available_sites, total_days
            )
            
            logger.info(f"AI selected {len(optimized_selection['selected_cities'])} destinations")
            
            return optimized_selection
            
        except Exception as e:
            logger.error(f"Error in destination selection: {e}")
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
        Creates the prompt for AI.
        """
        preferences_text = ""
        if preferences:
            preferences_text = f"\nUSER PREFERENCES:\n{json.dumps(preferences, indent=2)}"
        
        # Calculate suggested number of cities proportionally to days
        # Approximately 1 city every 3 days, with reasonable limits
        suggested_cities = max(1, min(int(round(total_days / 3.0)), 10))
        lower_bound = max(1, suggested_cities - 1)
        upper_bound = min(total_days, suggested_cities + 1)
        
        return f"""
        Select the best destinations for a trip to {country} for {total_days} days.

        AVAILABLE DESTINATIONS:
        {json.dumps(sites, indent=2)}

        {preferences_text}

        STRICT PLANNING RULES (do not change them):
        - Total trip days (user intention): {total_days}
        - The number of cities must be consistent with those days, avoiding ridiculous schedules (minimum 1 full day per city)
        - Consider transport time between cities (transport_days) and distribute the rest in exploration days
        - The SCHEDULER DOES NOT CHANGE user days: that's why you must choose a number of cities that allows using exactly {total_days} days
        - Practical rule: for {total_days} days, select between {lower_bound} and {upper_bound} cities, prioritizing variety and reasonable distances
        - Prioritize variety (capital, historical, nature/beach, etc.) and feasibility (reasonable distances)

        OUTPUT (JSON): return ONLY "selected_cities" with id, name, score and reason. Do not include days per city.
        """
    
    async def _optimize_selection(
        self, 
        ai_selection: Dict[str, Any], 
        available_sites: List[Dict[str, Any]], 
        total_days: int
    ) -> Dict[str, Any]:
        """
        Optimizes AI selection based on tourist relevance.
        """
        try:
            selected_cities = ai_selection.get("selected_cities", [])
            
            if not selected_cities:
                return ai_selection
            
            # Convert IDs/names to complete objects (site + AI fields)
            cities_with_data = []
            by_id = { str(site.get("_id") or site.get("id") or site.get("site_id") or ""): site for site in available_sites }
            by_name_lower = { (site.get("name") or "").lower(): site for site in available_sites }
            for city_info in selected_cities:
                site_obj = None
                city_id = (city_info.get("id") or "").strip()
                city_name = (city_info.get("name") or "").strip()
                if city_id and city_id in by_id:
                    site_obj = by_id[city_id].copy()
                elif city_name and city_name.lower() in by_name_lower:
                    site_obj = by_name_lower[city_name.lower()].copy()
                else:
                    logger.warning(f"LLM city without match by id or name: id='{city_id}', name='{city_name}'")
                    continue

                # Add only AI fields
                site_obj["score"] = float(city_info.get("score", 1))
                if "reason" in city_info:
                    site_obj["reason"] = city_info["reason"]
                cities_with_data.append(site_obj)
            
            # Sort by relevance score
            cities_with_data.sort(key=lambda x: x.get("score", 1), reverse=True)
            
            # Limit number of cities to a target range based on days
            suggested_cities = max(1, min(int(round(total_days / 3.0)), 10))
            lower_bound = max(1, suggested_cities - 1)
            upper_bound = min(total_days, suggested_cities + 1)
            # Also respect an absolute limit per segment to avoid huge responses
            if total_days <= 7:
                absolute_max = 6
            elif total_days <= 14:
                absolute_max = 10
            else:
                absolute_max = 15
            max_cities = min(upper_bound, absolute_max, len(cities_with_data))
            
            cities_with_data = cities_with_data[:max_cities]
            
            logger.info(f"Cities selected by relevance: {[c['name'] for c in cities_with_data]}")
            
            return {
                "selected_cities": cities_with_data,
                "total_cities": len(cities_with_data),
                "total_days": total_days
            }
        except Exception as e:
            logger.error(f"Error optimizing selection: {e}")
            return ai_selection

# Global instance
destination_selection_agent = DestinationSelectionAgent() 