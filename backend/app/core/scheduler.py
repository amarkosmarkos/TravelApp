"""
Scheduler central para gestión de presupuesto de tiempo y planificación de viajes.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

class CityVisit(BaseModel):
    """Modelo para una visita a una ciudad con tiempos específicos."""
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
    """Modelo completo del plan de viaje con línea temporal."""
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
    Gestor de presupuesto de tiempo para itinerarios de viaje.
    """
    
    def __init__(self, total_days: int, start_dt: datetime):
        self.total_hours = total_days * 24
        self.start_dt = start_dt
        self.avg_speed_kmh = 70  # velocidad promedio carretera
        
    def allocate_time(self, city_scores: List[Dict[str, Any]], 
                     transport_matrix: Dict[str, Dict[str, float]] = None) -> TravelPlan:
        """
        Asigna tiempo a las ciudades basándose en scores y matriz de transporte.
        """
        try:
            # 1. Reservar tiempo para llegada/salida
            arrival_day_hours = 8  # primer día: llegada
            departure_day_hours = 6  # último día: salida
            reserved_hours = arrival_day_hours + departure_day_hours
            
            # 2. Calcular horas disponibles para exploración
            available_explore_hours = self.total_hours - reserved_hours
            
            # 3. Calcular tiempo de transporte total
            total_transport_hours = self._calculate_total_transport_hours(
                city_scores, transport_matrix
            )
            
            # 4. Ajustar horas de exploración
            available_explore_hours -= total_transport_hours
            
            if available_explore_hours <= 0:
                logger.warning("Tiempo insuficiente para exploración")
                available_explore_hours = max(0, available_explore_hours)
            
            # 5. Distribuir horas de exploración según scores
            total_score = sum(city.get("score", 1) for city in city_scores)
            visits = []
            current_dt = self.start_dt + timedelta(hours=arrival_day_hours)
            
            for i, city in enumerate(city_scores):
                # Calcular horas de estancia proporcionales al score
                city_score = city.get("score", 1)
                explore_hours = (city_score / total_score) * available_explore_hours
                
                # Mínimo 1 día de estancia
                min_stay_hours = 24
                stay_hours = max(min_stay_hours, int(explore_hours))
                
                # Calcular transporte desde la ciudad anterior
                transport_hours = 0
                if i > 0 and transport_matrix:
                    prev_city = city_scores[i-1]["name"]
                    curr_city = city["name"]
                    transport_hours = transport_matrix.get(prev_city, {}).get(curr_city, 4)
                
                # Crear visita
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
                        "longitude": city.get("longitude") or city.get("lon")
                    }
                )
                
                visits.append(visit)
                current_dt = departure_dt + timedelta(hours=transport_hours)
            
            # Calcular fechas finales
            end_dt = current_dt + timedelta(hours=departure_day_hours)
            
            # Crear plan de viaje
            plan = TravelPlan(
                travel_id="",  # Se asignará después
                user_id="",    # Se asignará después
                origin_city="",
                start_dt=self.start_dt,
                end_dt=end_dt,
                visits=visits,
                total_travel_hours=total_transport_hours,
                total_explore_hours=sum(v.stay_hours for v in visits),
                preferences={}
            )
            
            logger.info(f"Plan creado: {len(visits)} ciudades, "
                       f"{plan.total_explore_hours:.1f}h exploración, "
                       f"{plan.total_travel_hours:.1f}h transporte")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error en allocate_time: {e}")
            raise
    
    def _calculate_total_transport_hours(self, city_scores: List[Dict[str, Any]], 
                                       transport_matrix: Dict[str, Dict[str, float]] = None) -> float:
        """
        Calcula el tiempo total de transporte entre ciudades.
        """
        if not transport_matrix or len(city_scores) <= 1:
            return 0
        
        total_hours = 0
        for i in range(len(city_scores) - 1):
            prev_city = city_scores[i]["name"]
            curr_city = city_scores[i + 1]["name"]
            
            # Usar matriz de transporte si está disponible
            if prev_city in transport_matrix and curr_city in transport_matrix[prev_city]:
                hours = transport_matrix[prev_city][curr_city]
            else:
                # Calcular usando coordenadas
                hours = self._calculate_transport_hours(
                    city_scores[i], city_scores[i + 1]
                )
            
            total_hours += hours
        
        return total_hours
    
    def _calculate_transport_hours(self, city1: Dict[str, Any], city2: Dict[str, Any]) -> float:
        """
        Calcula horas de transporte entre dos ciudades usando coordenadas.
        """
        try:
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
            logger.warning(f"Error calculando transporte {city1.get('name')} → {city2.get('name')}: {e}")
            return 4.0
    
    def create_transport_matrix(self, cities: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Crea matriz de tiempo de transporte entre todas las ciudades.
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
        Aplica una modificación al plan existente.
        """
        try:
            # Crear nueva lista de ciudades con scores
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
            
            # Aplicar modificaciones según el tipo
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
                        city["score"] = new_hours / 24  # convertir a score
                        break
            
            # Recrear plan con las modificaciones
            transport_matrix = self.create_transport_matrix(city_scores)
            new_plan = self.allocate_time(city_scores, transport_matrix)
            
            # Mantener IDs originales
            new_plan.travel_id = plan.travel_id
            new_plan.user_id = plan.user_id
            new_plan.origin_city = plan.origin_city
            new_plan.preferences = plan.preferences
            
            return new_plan
            
        except Exception as e:
            logger.error(f"Error aplicando modificación: {e}")
            return plan 