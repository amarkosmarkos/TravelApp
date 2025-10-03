"""
Service for calculating travel times between cities.
"""

import math
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class TravelTimeService:
    """
    Calculates realistic travel times between cities.
    """
    
    def __init__(self):
        # Average speeds in km/h (heuristics)
        self.speeds = {
            "local_bus": 50,       # Urban/local bus
            "intercity_bus": 75,   # Intercity bus
            "private_car": 85,     # Private transport
            "train": 120,          # Regional/medium distance train
            "flight_short": 750,   # Short/medium range plane
            "flight_long": 850     # Long range plane
        }
        
        # Additional times
        self.additional_times = {
            "airport_checkin_domestic": 1.5,  # check-in + airport transfer (domestic)
            "airport_checkin_international": 2.5,  # international
            "bus_station": 0.5,      # bus station arrival/departure
            "train_station": 0.5,    # train station arrival/departure
            "local_transport": 0.25  # local margin
        }
    
    def calculate_distance_km(self, coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
        """
        Calculates distance in km between two coordinates using Haversine formula.
        """
        try:
            lat1, lon1 = coord1["latitude"], coord1["longitude"]
            lat2, lon2 = coord2["latitude"], coord2["longitude"]
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Coordinate difference
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            # Haversine formula
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth radius in km
            r = 6371
            
            return c * r
            
        except Exception as e:
            logger.error(f"Error calculando distancia: {e}")
            return 0
    
    def estimate_travel_time(self, city1: Dict[str, Any], city2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estima tiempo real de viaje entre dos ciudades.
        """
        try:
            # Obtener coordenadas
            coord1 = city1.get("coordinates", {})
            coord2 = city2.get("coordinates", {})
            
            if not coord1 or not coord2:
                return {
                    "method": "unknown",
                    "duration": 0,
                    "airport_time": 0,
                    "total_time": 0,
                    "distance": 0
                }
            
            # Calcular distancia
            distance = self.calculate_distance_km(coord1, coord2)
            
            # Determine transport method and time (heuristic by segments)
            if distance < 80:
                method = "private_car"
                duration = distance / self.speeds[method] + self.additional_times["local_transport"]
                airport_time = 0
            elif distance < 200:
                method = "intercity_bus"
                duration = distance / self.speeds[method] + self.additional_times["bus_station"]
                airport_time = 0
            elif distance < 700:
                method = "train"
                duration = distance / self.speeds[method] + self.additional_times["train_station"]
                airport_time = 0
            elif distance < 2000:
                method = "flight"
                duration = distance / self.speeds["flight_short"]
                airport_time = self.additional_times["airport_checkin_domestic"]
            else:
                method = "flight"
                duration = distance / self.speeds["flight_long"]
                airport_time = self.additional_times["airport_checkin_international"]
            
            total_time = duration + airport_time
            
            return {
                "method": method,
                "duration": round(duration, 2),
                "airport_time": airport_time,
                "total_time": round(total_time, 2),
                "distance": round(distance, 2)
            }
            
        except Exception as e:
            logger.error(f"Error estimando tiempo de viaje: {e}")
            return {
                "method": "unknown",
                "duration": 0,
                "airport_time": 0,
                "total_time": 0,
                "distance": 0
            }
    
    def calculate_total_travel_time(self, cities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula tiempo total de transporte para una ruta.
        """
        if len(cities) < 2:
            return {
                "total_time": 0,
                "total_days": 0,
                "segments": []
            }
        
        total_time = 0
        segments = []
        
        for i in range(len(cities) - 1):
            city1 = cities[i]
            city2 = cities[i + 1]
            
            travel_info = self.estimate_travel_time(city1, city2)
            total_time += travel_info["total_time"]
            
            segments.append({
                "from": city1.get("name", "Unknown"),
                "to": city2.get("name", "Unknown"),
                "travel_info": travel_info
            })
        
        # Convert to days
        total_days = total_time / 24
        
        return {
            "total_time": round(total_time, 2),
            "total_days": round(total_days, 2),
            "segments": segments
        }

# Instancia global
travel_time_service = TravelTimeService() 