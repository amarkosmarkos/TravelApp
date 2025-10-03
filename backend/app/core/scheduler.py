"""
Central scheduler for time budget management and travel planning.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

class CityVisit(BaseModel):
    """Model for a city visit with specific times."""
    name: str
    arrival_dt: datetime
    departure_dt: datetime
    stay_hours: int
    transport_hours_from_prev: float = 0.0
    timezone: str = "UTC"
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class TravelPlan(BaseModel):
    """Complete travel plan model with timeline."""
    travel_id: str
    user_id: str
    origin_city: str
    start_dt: datetime
    end_dt: datetime
    visits: List[CityVisit]
    total_travel_hours: float
    total_explore_hours: float
    preferences: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class TimeBudgetScheduler:
    """
    Time budget manager for travel itineraries.
    """
    
    def __init__(self, total_days: int, start_dt: datetime, transport_provider: Optional[object] = None):
        self.total_hours = total_days * 24
        self.start_dt = start_dt
        self.avg_speed_kmh = 70  # average road speed
        self.transport_provider = transport_provider  # optional: external service
        
    def allocate_time(self, city_scores: List[Dict[str, Any]], 
                     transport_matrix: Dict[str, Dict[str, float]] = None) -> TravelPlan:
        """
        Allocates time to cities based on scores and transport matrix.
        """
        try:
            # 1. Calculate total transport time
            total_transport_hours = self._calculate_total_transport_hours(
                city_scores, transport_matrix
            )
            
            # 2. Use ALL available days for the trip
            total_available_days = self.total_hours / 24.0
            transport_days = total_transport_hours / 24.0
            available_explore_days = total_available_days - transport_days
            
            # 3. Distribute exploration days according to scores
            total_score = sum(city.get("score", 1) for city in city_scores)
            visits = []
            current_dt = self.start_dt
            
            for i, city in enumerate(city_scores):
                # Calculate stay days proportional to score
                city_score = city.get("score", 1)
                explore_days = (city_score / total_score) * available_explore_days
                
                # Minimum 1 day stay, round up
                min_stay_days = 1
                stay_days = max(min_stay_days, int(explore_days + 0.5))  # Round
                
                # Convert to hours for date calculations
                stay_hours = stay_days * 24
                
                # Calculate transportation from previous city
                transport_hours = 0
                if i > 0 and transport_matrix:
                    prev_city = city_scores[i-1]["name"]
                    curr_city = city["name"]
                    transport_hours = transport_matrix.get(prev_city, {}).get(curr_city, 4)
                
                # Create visit
                arrival_dt = current_dt
                departure_dt = arrival_dt + timedelta(hours=stay_hours)
                
                visit = CityVisit(
                    name=city["name"],
                    arrival_dt=arrival_dt,
                    departure_dt=departure_dt,
                    stay_hours=stay_hours,
                    transport_hours_from_prev=transport_hours,
                    metadata={
                        "score": city.get("score", 1),
                        "type": city.get("type", ""),
                        "description": city.get("description", ""),
                        "latitude": city.get("latitude") or city.get("lat"),
                        "longitude": city.get("longitude") or city.get("lon"),
                        "days": stay_days  # Add days for compatibility
                    }
                )
                
                visits.append(visit)
                current_dt = departure_dt + timedelta(hours=transport_hours)
            
            # Calculate final dates
            end_dt = current_dt
            
            # Create travel plan
            plan = TravelPlan(
                travel_id="",  # Will be assigned later
                user_id="",    # Will be assigned later
                origin_city="",
                start_dt=self.start_dt,
                end_dt=end_dt,
                visits=visits,
                total_travel_hours=total_transport_hours,
                total_explore_hours=sum(v.stay_hours for v in visits),
                preferences={}
            )
            
            logger.info(f"Plan created: {len(visits)} cities, "
                       f"{plan.total_explore_hours/24:.1f} exploration days, "
                       f"{plan.total_travel_hours/24:.1f} transport days, "
                       f"Total: {(plan.total_explore_hours + plan.total_travel_hours)/24:.1f} days")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error in allocate_time: {e}")
            raise
    
    def _calculate_total_transport_hours(self, city_scores: List[Dict[str, Any]], 
                                       transport_matrix: Dict[str, Dict[str, float]] = None) -> float:
        """
        Calculates total transport time between cities.
        """
        if not transport_matrix or len(city_scores) <= 1:
            return 0
        
        total_hours = 0
        for i in range(len(city_scores) - 1):
            prev_city = city_scores[i]["name"]
            curr_city = city_scores[i + 1]["name"]
            
            # Use transport matrix if available
            if prev_city in transport_matrix and curr_city in transport_matrix[prev_city]:
                hours = transport_matrix[prev_city][curr_city]
            else:
                # Calculate using coordinates
                hours = self._calculate_transport_hours(
                    city_scores[i], city_scores[i + 1]
                )
            
            total_hours += hours
        
        return total_hours
    
    def _calculate_transport_hours(self, city1: Dict[str, Any], city2: Dict[str, Any]) -> float:
        """
        Calculates transport hours between two cities using coordinates.
        """
        try:
            # If there's an external provider, try first
            if self.transport_provider and hasattr(self.transport_provider, "get_hours_between"):
                try:
                    hours = self.transport_provider.get_hours_between(city1, city2)
                    if isinstance(hours, (int, float)) and hours > 0:
                        return float(hours)
                except Exception as e:
                    logger.warning(f"Transport provider error: {e}")
            lat1 = city1.get("latitude") or city1.get("lat")
            lon1 = city1.get("longitude") or city1.get("lon")
            lat2 = city2.get("latitude") or city2.get("lat")
            lon2 = city2.get("longitude") or city2.get("lon")
            
            if lat1 and lon1 and lat2 and lon2:
                distance_km = geodesic((lat1, lon1), (lat2, lon2)).kilometers
                return distance_km / self.avg_speed_kmh
            else:
                return 4.0  # fallback
                
        except Exception as e:
            logger.warning(f"Error calculating transport {city1.get('name')} → {city2.get('name')}: {e}")
            return 4.0
    
    def create_transport_matrix(self, cities: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Creates transport time matrix between all cities.
        """
        matrix = {}
        
        for i, city1 in enumerate(cities):
            matrix[city1["name"]] = {}
            for j, city2 in enumerate(cities):
                if i != j:
                    hours = self._calculate_transport_hours(city1, city2)
                    matrix[city1["name"]][city2["name"]] = hours
        
        return matrix
    
    def apply_modification(self, plan: TravelPlan, modification: Dict[str, Any]) -> TravelPlan:
        """
        Applies a modification to the existing plan.
        """
        try:
            # Create new city list with scores
            city_scores = []
            for visit in plan.visits:
                city_scores.append({
                    "name": visit.name,
                    "score": visit.metadata.get("score", 1),
                    "type": visit.metadata.get("type", ""),
                    "description": visit.metadata.get("description", ""),
                    "latitude": visit.metadata.get("latitude"),
                    "longitude": visit.metadata.get("longitude")
                })
            
            # Apply modifications according to type
            if modification.get("action") == "add_city":
                new_city = modification.get("city", {})
                city_scores.append(new_city)
            
            elif modification.get("action") == "remove_city":
                city_name = modification.get("city_name", "")
                city_scores = [c for c in city_scores if c["name"] != city_name]
            
            elif modification.get("action") == "change_duration":
                city_name = modification.get("city_name", "")
                new_hours = modification.get("hours", 24)
                for city in city_scores:
                    if city["name"] == city_name:
                        city["score"] = new_hours / 24  # convert to score
                        break
            
            # Recreate plan with modifications
            transport_matrix = self.create_transport_matrix(city_scores)
            new_plan = self.allocate_time(city_scores, transport_matrix)
            
            # Keep original IDs
            new_plan.travel_id = plan.travel_id
            new_plan.user_id = plan.user_id
            new_plan.origin_city = plan.origin_city
            new_plan.preferences = plan.preferences
            
            return new_plan
            
        except Exception as e:
            logger.error(f"Error applying modification: {e}")
            return plan 