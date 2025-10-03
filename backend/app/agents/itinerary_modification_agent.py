"""
Agent specialized in modifying existing itineraries.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from app.database import get_itineraries_collection, get_itinerary_items_collection
from app.models.travel import Itinerary, ItineraryItem
from bson import ObjectId
import json
from pydantic import BaseModel, ValidationError
from app.services.daily_visits_service import daily_visits_service

logger = logging.getLogger(__name__)

class ItineraryModificationAgent:
    """
    Agent that modifies existing itineraries.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def modify_itinerary(self, 
                              itinerary_id: str,
                              modifications: Dict[str, Any],
                              user_id: str) -> Dict[str, Any]:
        """
        Modifies an existing itinerary according to specifications.
        """
        try:
            # Get current itinerary
            itineraries_collection = await get_itineraries_collection()
            current_itinerary = await itineraries_collection.find_one({
                "_id": ObjectId(itinerary_id),
                "user_id": user_id
            })
            
            if not current_itinerary:
                return {"error": "Itinerary not found"}
            
            # Apply modifications
            modified_itinerary = await self._apply_modifications(
                current_itinerary, modifications
            )
            
            # Update in database
            result = await itineraries_collection.update_one(
                {"_id": ObjectId(itinerary_id)},
                {
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "modifications": modifications,
                        "total_items": len(modified_itinerary.get("items", [])),
                        "last_modified_by": user_id
                    }
                }
            )
            
            # Update itinerary items
            await self._update_itinerary_items(itinerary_id, modified_itinerary.get("items", []))
            
            return {
                "success": True,
                "itinerary_id": itinerary_id,
                "modifications_applied": modifications,
                "total_items": len(modified_itinerary.get("items", [])),
                "updated_at": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error modifying itinerary: {e}")
            return {"error": str(e)}
    
    async def _apply_modifications(self, current_itinerary: Dict[str, Any], 
                                 modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies modifications to the current itinerary.
        """
        try:
            current_items = current_itinerary.get("items", [])
            modified_items = current_items.copy()
            
            # Apply changes according to modification type
            if modifications.get("action_type") == "add_cities":
                modified_items = await self._add_cities_to_itinerary(
                    current_items, modifications.get("cities_to_add", [])
                )
            
            elif modifications.get("action_type") == "remove_cities":
                modified_items = await self._remove_cities_from_itinerary(
                    current_items, modifications.get("cities_to_remove", [])
                )
            
            elif modifications.get("action_type") == "optimize_itinerary":
                modified_items = await self._optimize_itinerary_route(current_items)
            
            elif modifications.get("action_type") == "update_preferences":
                modified_items = await self._update_itinerary_preferences(
                    current_items, modifications.get("preferences", {})
                )
            
            # Recalculate days and order
            modified_items = self._recalculate_itinerary_days(modified_items)
            
            return {
                **current_itinerary,
                "items": modified_items,
                "total_items": len(modified_items),
                "last_modification": modifications
            }
            
        except Exception as e:
            self.logger.error(f"Error applying modifications: {e}")
            return current_itinerary
    
    async def _add_cities_to_itinerary(self, current_items: List[Dict], 
                                      cities_to_add: List[str]) -> List[Dict]:
        """
        Adds cities to the itinerary.
        """
        try:
            from app.agents.database_agent import DatabaseAgent
            from app.agents.routing_agent import RoutingAgent
            
            db_agent = DatabaseAgent()
            routing_agent = RoutingAgent()
            
            # Get information about cities to add
            new_items = []
            for city_name in cities_to_add:
                # Search for city information
                city_info = await db_agent.search_sites_by_city(city_name)
                if city_info:
                    new_items.append({
                        "city_name": city_name,
                        "city_id": city_info[0].get("id"),
                        "day": len(current_items) + len(new_items) + 1,
                        "activities": [],
                        "accommodation": "",
                        "transport": "",
                        "notes": f"Added by user modification"
                    })
            
            # Combine current items with new ones
            all_items = current_items + new_items
            
            # Optimize route if there are multiple cities
            if len(all_items) > 1:
                # Convert to routing format
                cities_for_routing = [
                    {"name": item["city_name"]} for item in all_items
                ]
                
                # Calculate optimized route
                optimized_route = routing_agent.calculate_route(cities_for_routing)
                
                # Reorder items according to optimized route
                optimized_items = []
                for i, city in enumerate(optimized_route.get("route", [])):
                    # Find corresponding item
                    for item in all_items:
                        if item["city_name"] == city["name"]:
                            item["day"] = i + 1
                            optimized_items.append(item)
                            break
                
                return optimized_items
            
            return all_items
            
        except Exception as e:
            self.logger.error(f"Error adding cities: {e}")
            return current_items
    
    async def _remove_cities_from_itinerary(self, current_items: List[Dict], 
                                           cities_to_remove: List[str]) -> List[Dict]:
        """
        Removes cities from the itinerary.
        """
        try:
            # Filter items that are not in the removal list
            remaining_items = [
                item for item in current_items 
                if item.get("city_name") not in cities_to_remove
            ]
            
            # Recalculate days
            for i, item in enumerate(remaining_items):
                item["day"] = i + 1
            
            return remaining_items
            
        except Exception as e:
            self.logger.error(f"Error removing cities: {e}")
            return current_items
    
    async def _optimize_itinerary_route(self, current_items: List[Dict]) -> List[Dict]:
        """
        Optimizes the itinerary route.
        """
        try:
            from app.agents.routing_agent import RoutingAgent
            
            routing_agent = RoutingAgent()
            
            # Convert to routing format
            cities_for_routing = [
                {"name": item["city_name"]} for item in current_items
            ]
            
            # Calculate optimized route
            optimized_route = routing_agent.calculate_route(cities_for_routing)
            
            # Reorder items according to optimized route
            optimized_items = []
            for i, city in enumerate(optimized_route.get("route", [])):
                # Find corresponding item
                for item in current_items:
                    if item["city_name"] == city["name"]:
                        item["day"] = i + 1
                        optimized_items.append(item)
                        break
            
            return optimized_items
            
        except Exception as e:
            self.logger.error(f"Error optimizing route: {e}")
            return current_items
    
    async def _update_itinerary_preferences(self, current_items: List[Dict], 
                                          preferences: Dict[str, Any]) -> List[Dict]:
        """
        Updates itinerary preferences.
        """
        try:
            # Update items with new preferences
            for item in current_items:
                item["preferences"] = preferences
                item["last_updated"] = datetime.utcnow()
            
            return current_items
            
        except Exception as e:
            self.logger.error(f"Error updating preferences: {e}")
            return current_items
    
    def _recalculate_itinerary_days(self, items: List[Dict]) -> List[Dict]:
        """
        Recalculates itinerary days.
        """
        try:
            from datetime import datetime, timedelta
            from geopy.distance import geodesic
            AVG_SPEED_KMH = 70
            # Determine start date: arrival of first city or now
            if items and items[0].get("arrival_dt"):
                current_dt = datetime.fromisoformat(items[0]["arrival_dt"])
            else:
                current_dt = datetime.utcnow()
            for i, item in enumerate(items):
                item["day"] = i + 1
                stay_days = item.get("days") or item.get("stay_days") or 1
                # Assign arrival if it doesn't exist or if we're recalculating
                item["arrival_dt"] = current_dt.isoformat()
                departure_dt = current_dt + timedelta(days=stay_days)
                item["departure_dt"] = departure_dt.isoformat()
                # Calculate transport to next
                if i < len(items) - 1:
                    next_item = items[i + 1]
                    if (item.get("latitude") or item.get("lat")) and (item.get("longitude") or item.get("lon")) and (next_item.get("latitude") or next_item.get("lat")) and (next_item.get("longitude") or next_item.get("lon")):
                        lat1 = item.get("latitude") or item.get("lat")
                        lon1 = item.get("longitude") or item.get("lon")
                        lat2 = next_item.get("latitude") or next_item.get("lat")
                        lon2 = next_item.get("longitude") or next_item.get("lon")
                        dist_km = geodesic((lat1, lon1), (lat2, lon2)).kilometers
                        travel_hours = dist_km / AVG_SPEED_KMH
                    else:
                        travel_hours = 4
                else:
                    travel_hours = 0
                item["transport_hours_to_next"] = travel_hours
                current_dt = departure_dt + timedelta(hours=travel_hours)
                item["updated_at"] = datetime.utcnow()
            return items
            
        except Exception as e:
            self.logger.error(f"Error recalculating days: {e}")
            return items
    
    async def _update_itinerary_items(self, itinerary_id: str, items: List[Dict]):
        """
        Updates itinerary items in the database.
        """
        try:
            items_collection = await get_itinerary_items_collection()
            
            # Delete existing items
            await items_collection.delete_many({"itinerary_id": itinerary_id})
            
            # Insert new items
            if items:
                for item in items:
                    item["itinerary_id"] = itinerary_id
                    item["created_at"] = datetime.utcnow()
                    item["updated_at"] = datetime.utcnow()
                
                await items_collection.insert_many(items)
            
        except Exception as e:
            self.logger.error(f"Error updating items: {e}")
    
    async def get_modification_history(self, itinerary_id: str) -> List[Dict[str, Any]]:
        """
        Gets the modification history of an itinerary.
        """
        try:
            itineraries_collection = await get_itineraries_collection()
            
            itinerary = await itineraries_collection.find_one({"_id": ObjectId(itinerary_id)})
            
            if itinerary:
                return {
                    "itinerary_id": itinerary_id,
                    "created_at": itinerary.get("created_at"),
                    "updated_at": itinerary.get("updated_at"),
                    "modifications": itinerary.get("modifications", []),
                    "total_modifications": len(itinerary.get("modifications", []))
                }
            else:
                return {"error": "Itinerary not found"}
                
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return {"error": str(e)} 
    
    async def analyze_modification_request(self, user_input: str) -> Dict[str, Any]:
        """
        Analyzes the user's modification request.
        """
        try:
            # Basic intention analysis
            user_input_lower = user_input.lower()
            
            # Detect modification type
            if any(word in user_input_lower for word in ["añadir", "agregar", "add", "añade", "agrega"]):
                intention = "add_cities"
            elif any(word in user_input_lower for word in ["quitar", "eliminar", "remove", "quit", "borrar"]):
                intention = "remove_cities"
            elif any(word in user_input_lower for word in ["optimizar", "optimize", "mejorar", "improve"]):
                intention = "optimize_route"
            elif any(word in user_input_lower for word in ["cambiar", "modificar", "change", "modify"]):
                intention = "modify_preferences"
            else:
                intention = "general_modification"
            
            # Extract mentioned cities (basic implementation)
            cities_mentioned = []
            # Here you could use NLP to extract city names
            # For now, we return an empty list

            # Extract requested days
            total_days = self._extract_days_from_text(user_input)

            # Extract preferred theme (history, beach, nature, food)
            theme = self._extract_theme_from_text(user_input)
            
            return {
                "intention": intention,
                "cities_mentioned": cities_mentioned,
                "user_input": user_input,
                "total_days": total_days,
                "theme": theme,
                "analysis": {
                    "action_type": intention,
                    "confidence": 0.7,
                    "requires_user_confirmation": False,
                    "total_days": total_days,
                    "theme": theme
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing modification request: {e}")
            return {
                "intention": "general_modification",
                "cities_mentioned": [],
                "user_input": user_input,
                "analysis": {
                    "action_type": "general_modification",
                    "confidence": 0.5,
                    "requires_user_confirmation": True
                }
            }

    def _extract_days_from_text(self, text: str) -> int:
        import re
        t = text.lower()
        patterns = [
            r"(\d+)\s*d[ií]as?",
            r"(\d+)\s*days?",
            r"one week|una semana",
            r"(\d+)\s*semanas?|(\d+)\s*weeks?",
            r"weekend|fin de semana"
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                if "week" in p or "semana" in p:
                    if "one" in p or "una" in p:
                        return 7
                    # take last group with number
                    num = next((int(g) for g in m.groups() if g and g.isdigit()), None)
                    if num:
                        return num * 7
                if "weekend" in p or "fin de semana" in p:
                    return 3
                if m.group(1):
                    return int(m.group(1))
        return 0

    def _extract_theme_from_text(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["history", "historic", "temple", "museum", "historia", "histórico", "historico", "templo", "museo"]):
            return "history"
        if any(k in t for k in ["beach", "island", "snorkel", "playa", "isla", "islas"]):
            return "beach"
        if any(k in t for k in ["nature", "mountain", "park", "hiking", "trekking", "naturaleza", "montaña", "parque", "senderismo"]):
            return "nature"
        if any(k in t for k in ["food", "restaurant", "gastronomy", "comida", "gastronom", "restaurante"]):
            return "food"
        return ""
    
    async def apply_modifications(self, existing_itinerary: Dict[str, Any], 
                                analysis: Dict[str, Any], available_sites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applies modifications using AI to understand intention and make intelligent changes.
        """
        try:
            logger.info(f"=== STARTING apply_modifications ===")
            logger.info(f"existing_itinerary keys: {list(existing_itinerary.keys())}")
            logger.info(f"existing_itinerary: {existing_itinerary}")
            logger.info(f"analysis: {analysis}")
            logger.info(f"available_sites count: {len(available_sites)}")
            
            user_input = analysis.get("user_input", "")
            
            # Search for travel_id in different ways
            travel_id = (
                existing_itinerary.get("travel_id")
                or (existing_itinerary.get("itinerary", {}).get("travel_id") if isinstance(existing_itinerary.get("itinerary"), dict) else None)
                or existing_itinerary.get("_id")
                or existing_itinerary.get("id")
            )
            
            if not travel_id:
                logger.error(f"travel_id not found in existing_itinerary")
                logger.error(f"Available keys: {list(existing_itinerary.keys())}")
                return {
                    "success": False,
                    "error": "Travel ID not found"
                }
            
            logger.info(f"Using travel_id: {travel_id}")
            
            # Get current itinerary from database
            itineraries_collection = await get_itineraries_collection()
            current_itinerary = await itineraries_collection.find_one({
                "travel_id": travel_id
            })
            
            if not current_itinerary:
                logger.error(f"Itinerary not found in DB for travel_id: {travel_id}")
                return {
                    "success": False,
                    "error": "Itinerary not found"
                }
            
            # Get current cities from itinerary
            current_cities = current_itinerary.get("cities", [])
            logger.info(f"Current cities in itinerary: {len(current_cities)}")
            
            # Use AI to understand the modification
            logger.info(f"Calling _analyze_modification_with_ai...")
            modification_result = await self._analyze_modification_with_ai(
                user_input, current_cities, available_sites
            )
            
            logger.info(f"AI result: {modification_result}")
            
            if modification_result.get("success"):
                # Apply changes suggested by AI
                modified_cities = modification_result.get("modified_cities", current_cities)

                # Filter by theme if requested (history/beach/nature/food)
                theme = analysis.get("theme") or analysis.get("analysis", {}).get("theme") or ""
                if theme:
                    theme_keywords = {
                        "history": ["temple", "templo", "museo", "ruins", "ruinas", "historic"],
                        "beach": ["beach", "playa", "island", "isla", "snorkel"],
                        "nature": ["park", "parque", "mountain", "montaña", "national"],
                        "food": ["food", "comida", "restaurant", "restaurante", "market", "mercado"]
                    }
                    keys = theme_keywords.get(theme, [])
                    def matches_theme(city: Dict[str, Any]) -> bool:
                        text = (city.get("description") or "") + " " + (city.get("type") or "") + " " + (city.get("name") or "")
                        t = text.lower()
                        return any(k in t for k in keys) if keys else True
                    # Keep cities that match and, if too few remain, include originals again
                    themed = [c for c in modified_cities if matches_theme(c)]
                    if len(themed) >= 2:
                        modified_cities = themed

                # Redistribute days to requested total (if exists), maintaining minimum 1 day per city
                requested_days = analysis.get("total_days") or analysis.get("analysis", {}).get("total_days") or 0
                if requested_days and requested_days > 0 and modified_cities:
                    per_city = max(1, requested_days // len(modified_cities))
                    remainder = max(0, requested_days - per_city * len(modified_cities))
                    for idx, city in enumerate(modified_cities):
                        base_days = per_city + (1 if idx < remainder else 0)
                        city["days"] = base_days

                # If no days in cities, assign 2 by default and then normalize to <= 14
                if modified_cities and not any(c.get("days") for c in modified_cities):
                    for c in modified_cities:
                        c["days"] = 2

                # Normalize coordinate keys
                for c in modified_cities:
                    if c.get("lat") and not c.get("latitude"):
                        c["latitude"] = c.get("lat")
                    if c.get("lon") and not c.get("longitude"):
                        c["longitude"] = c.get("lon")

                # Update itinerary in database
                await itineraries_collection.update_one(
                    {"travel_id": travel_id},
                    {
                        "$set": {
                            "cities": modified_cities,
                            "updated_at": datetime.utcnow(),
                            "total_items": len(modified_cities)
                        }
                    }
                )

                logger.info(f"Itinerary updated by AI: {len(modified_cities)} cities")

                # Regenerate daily_visits for travel
                try:
                    await daily_visits_service.generate_and_save_for_travel(str(travel_id))
                except Exception as e:
                    self.logger.error(f"Error regenerating daily_visits: {e}")

                # Message with correct pluralization
                total_cities = len(modified_cities)
                plural = "city" if total_cities == 1 else "cities"

                return {
                    "success": True,
                    "action": "ai_modification",
                    "message": modification_result.get("message", f"Itinerary updated by AI: {total_cities} {plural}"),
                    "itinerary": {
                        "cities": modified_cities,
                        "total_items": total_cities,
                        "updated_at": datetime.utcnow()
                    }
                }
            else:
                logger.error(f"AI error: {modification_result.get('error')}")
                return {
                    "success": False,
                    "error": modification_result.get("error", "Could not process modification")
                }
                
        except Exception as e:
            logger.error(f"Error applying modifications: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_modification_with_ai(self, user_input: str, current_cities: List[Dict], 
                                          available_sites: List[Dict]) -> Dict[str, Any]:
        """
        Uses AI to analyze the modification and suggest changes.
        """
        try:
            logger.info(f"Analyzing modification with AI: {user_input}")
            logger.info(f"Current cities: {len(current_cities)}")
            logger.info(f"Available sites: {len(available_sites)}")
            
            from openai import AzureOpenAI
            from app.config import settings
            
            client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
            
            # Prepare data for AI
            current_cities_formatted = [
                {
                    "name": city.get("name", ""),
                    "days": city.get("days", 1),
                    "type": city.get("type", ""),
                    "description": city.get("description", "")
                }
                for city in current_cities
            ]
            
            available_sites_formatted = [
                {
                    "name": site.get("name", ""),
                    "type": site.get("type", ""),
                    "description": site.get("description", ""),
                    "coordinates": {
                        "latitude": float(site.get("lat", 0)) if site.get("lat") else 0,
                        "longitude": float(site.get("lon", 0)) if site.get("lon") else 0
                    }
                }
                for site in available_sites
            ]
            
            logger.info(f"Data prepared for AI")
            
            # Create prompt for AI
            prompt = f"""
            Analyze the user's modification request and suggest changes to the itinerary.

            USER REQUEST: "{user_input}"

            CURRENT ITINERARY:
            {current_cities_formatted}

            AVAILABLE SITES:
            {available_sites_formatted}

            INSTRUCTIONS:
            1. Understand user intention (change, add, remove cities)
            2. Identify mentioned cities
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
                        "reason": "reason for change"
                    }}
                ],
                "modified_cities": [
                    {{
                        "name": "city name",
                        "days": number of days,
                        "type": "site type",
                        "description": "description"
                    }}
                ],
                "message": "explanatory message of changes"
            }}
            """
            
            logger.info(f"Calling AI...")
            
            # Call AI
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel planning expert. Analyze itinerary modification requests and suggest intelligent changes."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            logger.info(f"AI response received")
            
            # Pydantic models to validate output
            class Change(BaseModel):
                action: str
                city_name: str
                reason: str | None = None

            class ModifiedCity(BaseModel):
                name: str
                days: int | float | None = None
                type: str | None = None
                description: str | None = None

            class ModResult(BaseModel):
                intention: str
                changes: List[Change] = []
                modified_cities: List[ModifiedCity] = []
                message: str | None = None

            # Process response
            response_content = response.choices[0].message.content or ""
            logger.info(f"Raw response content: {response_content[:200]}...")

            # Remove possible markdown blocks ```json ... ``` and validate JSON
            import re
            cleaned = re.sub(r"```[a-zA-Z]*", "", response_content).replace("```", "").strip()
            
            logger.info(f"Cleaned content: {cleaned[:200]}...")
            # Try to parse with tolerance
            try:
                result_raw = json.loads(cleaned)
            except Exception:
                # Try to extract first JSON block between braces
                import re as _re
                match = _re.search(r"\{[\s\S]*\}", cleaned)
                if not match:
                    raise
                result_raw = json.loads(match.group(0))

            # Validate against schema
            try:
                validated = ModResult(**result_raw)
            except ValidationError as ve:
                logger.error(f"Invalid AI response: {ve}")
                return {"success": False, "error": "Invalid AI response"}
            
            # Apply changes suggested by AI
            modified_cities = []
            
            for city_data in validated.modified_cities:
                # Search for corresponding site in available_sites
                site_data = None
                for site in available_sites:
                    if site.get("name", "").lower() == (city_data.name or "").lower():
                        site_data = site.copy()
                        site_data["days"] = int(city_data.days) if city_data.days else 2
                        break
                
                if site_data:
                    modified_cities.append(site_data)
            
            logger.info(f"Modified cities: {len(modified_cities)}")
            
            return {
                "success": True,
                "modified_cities": modified_cities,
                "message": validated.message or "Itinerary updated by AI",
                "intention": validated.intention or "modification"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing modification with AI: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            } 