"""
Servicio para calcular tiempos de viaje entre ciudades.
"""

import math
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class TravelTimeService:
    """
    Calcula tiempos de viaje realistas entre ciudades.
    """
    
    def __init__(self):
        # Velocidades promedio en km/h
        self.speeds = {
            "local_bus": 60,      # Bus local
            "intercity_bus": 80,  # Bus interurbano
            "car": 90,            # Coche
            "flight": 800         # Velocidad promedio avión
        }
        
        # Tiempos adicionales
        self.additional_times = {
            "airport_checkin": 2,    # Horas para check-in + ir al aeropuerto
            "bus_station": 0.5,      # Horas para ir a estación de bus
            "local_transport": 0.25  # Horas para transporte local
        }
    
    def calculate_distance_km(self, coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
        """
        Calcula distancia en km entre dos coordenadas usando fórmula de Haversine.
        """
        try:
            lat1, lon1 = coord1["latitude"], coord1["longitude"]
            lat2, lon2 = coord2["latitude"], coord2["longitude"]
            
            # Convertir a radianes
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Diferencia de coordenadas
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            # Fórmula de Haversine
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Radio de la Tierra en km
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
            
            # Determinar método de transporte y tiempo
            if distance < 100:
                # Bus/coche local
                method = "local_bus"
                duration = distance / self.speeds[method]
                airport_time = 0
                
            elif distance < 500:
                # Bus interurbano
                method = "intercity_bus"
                duration = distance / self.speeds[method]
                airport_time = self.additional_times["bus_station"]
                
            else:
                # Avión obligatorio para distancias largas
                method = "flight"
                duration = 4  # 4 horas de vuelo para distancias > 500km
                airport_time = self.additional_times["airport_checkin"]
            
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
        
        # Convertir a días
        total_days = total_time / 24
        
        return {
            "total_time": round(total_time, 2),
            "total_days": round(total_days, 2),
            "segments": segments
        }

# Instancia global
travel_time_service = TravelTimeService() 