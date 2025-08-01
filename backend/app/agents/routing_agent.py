"""
Agente especializado en cálculo de rutas óptimas usando grafos y algoritmos de optimización.
"""

from typing import List, Dict, Any, Tuple
import networkx as nx
import numpy as np
from geopy.distance import geodesic
import logging
import json

logger = logging.getLogger(__name__)

class RoutingAgent:
    """
    Agente especializado en cálculo de rutas óptimas entre ciudades.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_route(self, cities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula la ruta óptima entre las ciudades proporcionadas.
        """
        try:
            if len(cities) < 2:
                return {
                    "route": cities,
                    "total_distance": 0,
                    "estimated_time": 0,
                    "algorithm": "direct"
                }
            
            # Crear grafo con las ciudades
            G = self._create_city_graph(cities)
            
            # Calcular ruta óptima usando diferentes algoritmos
            routes = {}
            
            # 1. TSP (Traveling Salesman Problem) - Ruta circular
            tsp_route = self._solve_tsp(G, cities)
            routes["tsp"] = tsp_route
            
            # 2. Ruta más corta entre puntos específicos
            shortest_route = self._find_shortest_path(G, cities)
            routes["shortest"] = shortest_route
            
            # 3. Ruta basada en proximidad geográfica
            proximity_route = self._route_by_proximity(cities)
            routes["proximity"] = proximity_route
            
            # Seleccionar la mejor ruta (por defecto TSP)
            best_route = tsp_route
            
            return {
                "route": best_route["cities"],
                "total_distance": best_route["total_distance"],
                "estimated_time": best_route["estimated_time"],
                "algorithm": best_route["algorithm"],
                "alternative_routes": routes
            }
            
        except Exception as e:
            self.logger.error(f"Error calculando ruta: {e}")
            return {
                "route": cities,
                "total_distance": 0,
                "estimated_time": 0,
                "algorithm": "fallback",
                "error": str(e)
            }
    
    def _create_city_graph(self, cities: List[Dict[str, Any]]) -> nx.Graph:
        """
        Crea un grafo con las ciudades y sus distancias.
        """
        G = nx.Graph()
        
        # Agregar nodos
        for city in cities:
            G.add_node(city["name"], **city)
        
        # Agregar aristas con distancias
        for i, city1 in enumerate(cities):
            for j, city2 in enumerate(cities[i+1:], i+1):
                if (city1.get("latitude") and city1.get("longitude") and 
                    city2.get("latitude") and city2.get("longitude")):
                    
                    distance = geodesic(
                        (city1["latitude"], city1["longitude"]),
                        (city2["latitude"], city2["longitude"])
                    ).kilometers
                    
                    G.add_edge(city1["name"], city2["name"], weight=distance)
        
        return G
    
    def _solve_tsp(self, G: nx.Graph, cities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resuelve el problema del viajante (TSP) para encontrar la ruta circular óptima.
        """
        try:
            # Usar algoritmo de aproximación para TSP
            if len(cities) <= 2:
                route_cities = cities
                total_distance = 0
                if len(cities) == 2:
                    total_distance = geodesic(
                        (cities[0]["latitude"], cities[0]["longitude"]),
                        (cities[1]["latitude"], cities[1]["longitude"])
                    ).kilometers
            else:
                # Algoritmo de aproximación: Nearest Neighbor
                route_cities = self._nearest_neighbor_tsp(cities)
                total_distance = self._calculate_route_distance(route_cities)
            
            # Estimar tiempo de viaje (asumiendo velocidad promedio de 80 km/h)
            estimated_time = total_distance / 80  # horas
            
            return {
                "cities": route_cities,
                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "algorithm": "tsp_nearest_neighbor"
            }
            
        except Exception as e:
            self.logger.error(f"Error en TSP: {e}")
            return {
                "cities": cities,
                "total_distance": 0,
                "estimated_time": 0,
                "algorithm": "tsp_fallback"
            }
    
    def _nearest_neighbor_tsp(self, cities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Implementa el algoritmo del vecino más cercano para TSP.
        """
        if len(cities) <= 1:
            return cities
        
        unvisited = cities.copy()
        route = [unvisited.pop(0)]  # Empezar con la primera ciudad
        
        while unvisited:
            current_city = route[-1]
            nearest_city = None
            min_distance = float('inf')
            
            for city in unvisited:
                if (current_city.get("latitude") and current_city.get("longitude") and
                    city.get("latitude") and city.get("longitude")):
                    
                    distance = geodesic(
                        (current_city["latitude"], current_city["longitude"]),
                        (city["latitude"], city["longitude"])
                    ).kilometers
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_city = city
            
            if nearest_city:
                route.append(nearest_city)
                unvisited.remove(nearest_city)
            else:
                # Si no se puede calcular distancia, agregar la primera ciudad no visitada
                route.append(unvisited.pop(0))
        
        return route
    
    def _find_shortest_path(self, G: nx.Graph, cities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Encuentra la ruta más corta entre las ciudades.
        """
        try:
            if len(cities) < 2:
                return {
                    "cities": cities,
                    "total_distance": 0,
                    "estimated_time": 0,
                    "algorithm": "shortest_path"
                }
            
            # Usar Dijkstra para encontrar la ruta más corta
            start_city = cities[0]["name"]
            end_city = cities[-1]["name"]
            
            try:
                shortest_path = nx.shortest_path(G, start_city, end_city, weight='weight')
                total_distance = nx.shortest_path_length(G, start_city, end_city, weight='weight')
            except nx.NetworkXNoPath:
                # Si no hay camino directo, usar TSP
                return self._solve_tsp(G, cities)
            
            # Mapear nombres de ciudades a objetos completos
            route_cities = []
            for city_name in shortest_path:
                city_obj = next((c for c in cities if c["name"] == city_name), None)
                if city_obj:
                    route_cities.append(city_obj)
            
            estimated_time = total_distance / 80  # horas
            
            return {
                "cities": route_cities,
                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "algorithm": "shortest_path"
            }
            
        except Exception as e:
            self.logger.error(f"Error en shortest path: {e}")
            return {
                "cities": cities,
                "total_distance": 0,
                "estimated_time": 0,
                "algorithm": "shortest_path_fallback"
            }
    
    def _route_by_proximity(self, cities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea una ruta basada en proximidad geográfica.
        """
        try:
            if len(cities) <= 1:
                return {
                    "cities": cities,
                    "total_distance": 0,
                    "estimated_time": 0,
                    "algorithm": "proximity"
                }
            
            # Ordenar ciudades por proximidad al centro geográfico
            center_lat = np.mean([c.get("latitude", 0) for c in cities])
            center_lon = np.mean([c.get("longitude", 0) for c in cities])
            
            # Calcular distancia al centro para cada ciudad
            for city in cities:
                if city.get("latitude") and city.get("longitude"):
                    distance_to_center = geodesic(
                        (center_lat, center_lon),
                        (city["latitude"], city["longitude"])
                    ).kilometers
                    city["distance_to_center"] = distance_to_center
                else:
                    city["distance_to_center"] = float('inf')
            
            # Ordenar por distancia al centro
            sorted_cities = sorted(cities, key=lambda x: x.get("distance_to_center", float('inf')))
            
            total_distance = self._calculate_route_distance(sorted_cities)
            estimated_time = total_distance / 80  # horas
            
            return {
                "cities": sorted_cities,
                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "algorithm": "proximity"
            }
            
        except Exception as e:
            self.logger.error(f"Error en route by proximity: {e}")
            return {
                "cities": cities,
                "total_distance": 0,
                "estimated_time": 0,
                "algorithm": "proximity_fallback"
            }
    
    def _calculate_route_distance(self, route_cities: List[Dict[str, Any]]) -> float:
        """
        Calcula la distancia total de una ruta.
        """
        total_distance = 0
        
        for i in range(len(route_cities) - 1):
            city1 = route_cities[i]
            city2 = route_cities[i + 1]
            
            if (city1.get("latitude") and city1.get("longitude") and
                city2.get("latitude") and city2.get("longitude")):
                
                distance = geodesic(
                    (city1["latitude"], city1["longitude"]),
                    (city2["latitude"], city2["longitude"])
                ).kilometers
                
                total_distance += distance
        
        return total_distance
    
    def optimize_for_time(self, cities: List[Dict[str, Any]], max_days: int = 7) -> Dict[str, Any]:
        """
        Optimiza la ruta considerando tiempo disponible.
        """
        try:
            # Calcular tiempo estimado por ciudad (asumiendo 1 día por ciudad)
            estimated_days = len(cities)
            
            if estimated_days <= max_days:
                # Si hay tiempo suficiente, usar ruta completa
                return self.calculate_route(cities)
            else:
                # Si no hay tiempo suficiente, seleccionar ciudades más importantes
                # Por ahora, seleccionar las primeras max_days ciudades
                selected_cities = cities[:max_days]
                return self.calculate_route(selected_cities)
                
        except Exception as e:
            self.logger.error(f"Error optimizando por tiempo: {e}")
            return self.calculate_route(cities) 