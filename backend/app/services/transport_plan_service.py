"""
Service for generating and saving the transport plan for a trip.

Rules/Heuristics:
- Outbound flight: Home -> first city (if there are cities)
- Return flight: last city -> Home
- Between cities: select mode based on approximate distance:
  < 80km: private_car | local_bus
  < 200km: intercity_bus | train (simple heuristic: if both cities >300k pop? omitted, we use bus by default)
  < 500km: train preferred; if not, intercity_bus
  >= 500km: flight
- If detects "island" in metadata/type/name and distance < 300km: boat

Budget: heuristic cost per mode and per km/segment.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.database import (
    get_travels_collection,
    get_itineraries_collection,
)
from app.services.travel_time_service import TravelTimeService

logger = logging.getLogger(__name__)


class TransportPlanService:
    def __init__(self) -> None:
        self.time_service = TravelTimeService()
        # Heuristic costs (generic currency)
        self.costs_per_km = {
            "local_bus": 0.07,
            "intercity_bus": 0.10,
            "train": 0.16,
            "private_car": 0.30,   # more expensive per km
            "boat": 0.18,
            "flight": 0.12,        # lower cost per km, but with high fixed cost
        }
        self.flat_cost = {
            "flight_domestic": 60.0,
            "flight_international": 180.0,
            "boat": 15.0,
        }

    async def generate_and_save_for_travel(self, travel_id: str) -> bool:
        try:
            travels = await get_travels_collection()
            itineraries = await get_itineraries_collection()

            travel = await travels.find_one({"_id": travel_id})
            if not travel:
                # cuando travel_id es str del ObjectId en otras rutas, normalizamos
                from bson import ObjectId
                try:
                    travel = await travels.find_one({"_id": ObjectId(travel_id)})
                except Exception:
                    travel = None
            if not travel:
                logger.warning(f"TransportPlan: travel not found {travel_id}")
                return False

            itinerary = await itineraries.find_one({"travel_id": str(travel_id)})
            if not itinerary:
                logger.warning(f"TransportPlan: itinerary not found for travel {travel_id}")
                return False

            cities: List[Dict[str, Any]] = itinerary.get("cities") or []
            segments: List[Dict[str, Any]] = []

            def _coord(city: Dict[str, Any]) -> Optional[Dict[str, float]]:
                # Normalizar coordenadas desde distintas claves
                if isinstance(city.get("coordinates"), dict):
                    lat = city["coordinates"].get("latitude") or city["coordinates"].get("lat")
                    lon = city["coordinates"].get("longitude") or city["coordinates"].get("lon")
                else:
                    lat = city.get("latitude") or city.get("lat") or (city.get("metadata") or {}).get("latitude")
                    lon = city.get("longitude") or city.get("lon") or (city.get("metadata") or {}).get("longitude")
                try:
                    if lat is None or lon is None:
                        return None
                    return {"latitude": float(lat), "longitude": float(lon)}
                except Exception:
                    return None

            def _is_island(city: Dict[str, Any]) -> bool:
                name = (city.get("name") or "").lower()
                typev = (city.get("type") or "").lower()
                desc = (city.get("description") or "").lower()
                return any(k in name or k in typev or k in desc for k in ["island", "isla", "islas", "archipelago", "archipiélago"])  # heuristic

            def _estimate_segment(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
                coord_a = _coord(a) or {}
                coord_b = _coord(b) or {}
                # TravelTimeService espera coord en city["coordinates"]
                a_wrapped = {"coordinates": coord_a}
                b_wrapped = {"coordinates": coord_b}
                est = self.time_service.estimate_travel_time(a_wrapped, b_wrapped)
                distance = est.get("distance", 0.0)
                method = est.get("method", "intercity_bus")
                # Ajuste por islas
                if (_is_island(a) or _is_island(b)) and distance and distance < 300:
                    method = "boat"
                # Presupuesto
                extra = 0.0
                if method == "flight":
                    extra = self.flat_cost["flight_domestic"] if distance < 2000 else self.flat_cost["flight_international"]
                elif method == "boat":
                    extra = self.flat_cost["boat"]
                cost = round(distance * self.costs_per_km.get(method, 0.15) + extra, 2)
                return {
                    "from": a.get("name"),
                    "to": b.get("name"),
                    "method": method,
                    "distance_km": distance,
                    "duration_h": round(est.get("total_time", est.get("duration", 0) + est.get("airport_time", 0)), 2),
                    "details": est,
                    "estimated_cost": cost,
                }

            # Vuelo de ida (Home -> primera ciudad) — opcional con distancia si se configuran coords de Home
            if cities:
                first = cities[0]
                home_coords = None
                try:
                    from app.config import settings
                    # If HOME_LAT/HOME_LON variables exist, use them
                    home_lat = float(getattr(settings, "HOME_LAT", 0) or 0)
                    home_lon = float(getattr(settings, "HOME_LON", 0) or 0)
                    if home_lat and home_lon:
                        home_coords = {"latitude": home_lat, "longitude": home_lon}
                except Exception:
                    home_coords = None

                if home_coords and _coord(first):
                    est_out = self.time_service.estimate_travel_time({"coordinates": home_coords}, {"coordinates": _coord(first)})
                    dist_out = est_out.get("distance", 0)
                    dur_out = round(est_out.get("total_time", 0), 2)
                else:
                    dist_out = 0
                    # Reasonable default value for international flight duration if no coordinates
                    dur_out = 10.0

                segments.append({
                    "from": "Home",
                    "to": first.get("name"),
                    "method": "flight",
                    "distance_km": round(dist_out, 2),
                    "duration_h": dur_out,
                    "details": {},
                    "estimated_cost": round((dist_out * self.costs_per_km["flight"]) + self.flat_cost["flight_international"], 2) if dist_out else 600.0,
                })

            # Entre ciudades
            for i in range(len(cities) - 1):
                a = cities[i]
                b = cities[i + 1]
                try:
                    segments.append(_estimate_segment(a, b))
                except Exception as e:
                    logger.warning(f"TransportPlan: error estimating segment {a.get('name')}->{b.get('name')}: {e}")

            # Return flight (last city -> Home)
            if cities:
                last = cities[-1]
                home_coords = None
                try:
                    from app.config import settings
                    home_lat = float(getattr(settings, "HOME_LAT", 0) or 0)
                    home_lon = float(getattr(settings, "HOME_LON", 0) or 0)
                    if home_lat and home_lon:
                        home_coords = {"latitude": home_lat, "longitude": home_lon}
                except Exception:
                    home_coords = None

                if home_coords and _coord(last):
                    est_back = self.time_service.estimate_travel_time({"coordinates": _coord(last)}, {"coordinates": home_coords})
                    dist_back = est_back.get("distance", 0)
                    dur_back = round(est_back.get("total_time", 0), 2)
                else:
                    dist_back = 0
                    dur_back = 10.0

                segments.append({
                    "from": last.get("name"),
                    "to": "Home",
                    "method": "flight",
                    "distance_km": round(dist_back, 2),
                    "duration_h": dur_back,
                    "details": {},
                    "estimated_cost": round((dist_back * self.costs_per_km["flight"]) + self.flat_cost["flight_international"], 2) if dist_back else 600.0,
                })

            totals = {
                "segments": len(segments),
                "total_distance_km": round(sum((s.get("distance_km") or 0) for s in segments), 2),
                "total_duration_h": round(sum((s.get("duration_h") or 0) for s in segments), 2),
                "total_cost": round(sum((s.get("estimated_cost") or 0) for s in segments), 2),
            }

            plan = {
                "generated_at": datetime.utcnow().isoformat(),
                "segments": segments,
                "totals": totals,
            }

            # Guardar embebido en el itinerario
            await itineraries.update_one(
                {"travel_id": str(travel_id)},
                {"$set": {"transport_plan": plan, "transport_plan_generated_at": datetime.utcnow().isoformat()}}
            )

            logger.info(f"TransportPlan: generated {len(segments)} segments for travel {travel_id}")
            return True
        except Exception as e:
            logger.error(f"Error generating transport plan for {travel_id}: {e}")
            return False


transport_plan_service = TransportPlanService()


