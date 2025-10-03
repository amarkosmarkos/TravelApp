from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field

from app.database import get_itineraries_collection
from app.agents.database_agent import DatabaseAgent
from app.config import settings
from difflib import SequenceMatcher


logger = logging.getLogger(__name__)


class VisitItem(BaseModel):
    id: str
    time: str
    place_id: str | None = None
    place_name: str
    category: str | None = None
    coordinates: Dict[str, float] | None = None
    notes: str | None = None
    duration_min: int | None = None


class DaySchedule(BaseModel):
    day_index: int = Field(ge=1)
    date: str
    city: str
    window: Dict[str, str]
    items: List[VisitItem] = []


class DailyVisitsService:
    """
    Service for generating and saving daily visits (daily_visits) nested in the itinerary.
    Maintains compatibility: if LLM fails or is not configured, uses deterministic heuristics.
    """

    def __init__(self) -> None:
        self.db_agent = DatabaseAgent()

    async def generate_and_save_for_travel(self, travel_id: str) -> bool:
        try:
            itineraries = await get_itineraries_collection()
            itinerary = await itineraries.find_one({"travel_id": travel_id})
            if not itinerary:
                logger.warning(f"No itinerary found for travel_id={travel_id}")
                return False

            daily_visits = await self._generate_daily_visits_for_itinerary(itinerary)

            # Save embedded
            await itineraries.update_one(
                {"travel_id": travel_id},
                {"$set": {"daily_visits": [dv.model_dump() for dv in daily_visits], "updated_at": datetime.utcnow()}}
            )
            logger.info(f"daily_visits generated: {len(daily_visits)} days for travel {travel_id}")
            return True
        except Exception as e:
            logger.error(f"Error generating daily_visits: {e}")
            return False

    async def _generate_daily_visits_for_itinerary(self, itinerary: Dict[str, Any]) -> List[DaySchedule]:
        cities = itinerary.get("cities", [])
        itinerary_text = itinerary.get("itinerary") or ""
        day_schedules: List[DaySchedule] = []
        current_day_index = 1

        for city in cities:
            city_name = city.get("name") or city.get("city_name") or ""
            arrival_iso = city.get("arrival_dt")
            departure_iso = city.get("departure_dt")

            # Calculate number of days per city
            num_days = 1
            try:
                if arrival_iso and departure_iso:
                    arr = datetime.fromisoformat(arrival_iso.replace("Z", "+00:00"))
                    dep = datetime.fromisoformat(departure_iso.replace("Z", "+00:00"))
                    total_hours = max((dep - arr).total_seconds() / 3600.0, 0.0)
                    num_days = max(1, int((total_hours + 23.999) // 24))
                else:
                    # fallback by stay_hours or days
                    stay_hours = city.get("stay_hours")
                    if stay_hours:
                        num_days = max(1, int((float(stay_hours) + 23.999) // 24))
                    else:
                        num_days = int(city.get("days") or city.get("stay_days") or 1)
            except Exception:
                num_days = int(city.get("days") or 1)

            # We NO LONGER query DB or generate candidates: only extract strings from the global itinerary

            # Heuristic: 4 visits per day (morning, midday, afternoon, evening)
            default_slots = ["09:00", "12:30", "16:00", "19:30"]
            cand_idx = 0

            # Starting point
            start_dt = None
            try:
                if arrival_iso:
                    start_dt = datetime.fromisoformat(arrival_iso.replace("Z", "+00:00"))
            except Exception:
                start_dt = datetime.utcnow()

            for i in range(num_days):
                day_date = (start_dt + timedelta(days=i)) if start_dt else datetime.utcnow()
                # Try LLM generation per day; if it fails, use heuristics
                items: List[VisitItem] = []
                day_window = {
                    "start": (day_date.replace(hour=9, minute=0, second=0, microsecond=0)).isoformat(),
                    "end": (day_date.replace(hour=21, minute=0, second=0, microsecond=0)).isoformat()
                }

                # ONLY step: extraction from the complete itinerary text
                extracted_items: List[Dict[str, Any]] = []
                if itinerary_text:
                    try:
                        extracted_items = self._extract_city_items_from_itinerary_text(
                            city_name, day_window, itinerary_text
                        )
                        if extracted_items:
                            for idx, it in enumerate(extracted_items, start=1):
                                items.append(VisitItem(
                                    id=f"visit-{current_day_index}-{idx}",
                                    time=it.get("time") or default_slots[min(idx-1, len(default_slots)-1)],
                                    place_id=None,
                                    place_name=it.get("place_name", f"Activity in {city_name}"),
                                    category=it.get("category", "visit"),
                                    coordinates=None,
                                    duration_min=int(it.get("duration_min") or 90)
                                ))
                    except Exception as e:
                        logger.warning(f"Extraction from itinerary text failed: {e}")

                # If no extraction, we don't invent or query anything → the day remains without items

                day_schedule = DaySchedule(
                    day_index=current_day_index,
                    date=day_date.date().isoformat(),
                    city=city_name,
                    window=day_window,
                    items=items
                )
                day_schedules.append(day_schedule)
                current_day_index += 1

        return day_schedules

    def _extract_city_items_from_itinerary_text(self, city: str, window: Dict[str, str], itinerary_text: str) -> List[Dict[str, Any]]:
        """
        Uses LLM to extract items (time, place_name, category?, duration_min?) from the complete itinerary text
        only for the specified city and approximate time range of the day. Returns list of dicts.
        """
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )

            system = (
                "You are an itinerary entity extractor. Return ONLY valid JSON with 'items'.\n"
                "Each item: {time:'HH:MM' optional, place_name:string, category?:string, duration_min?:number}.\n"
                "Don't invent ids, don't return HTML. Limit yourself to the specified city."
            )
            user = (
                f"Complete itinerary text (may include multiple cities):\n\n{itinerary_text}\n\n"
                f"Extract ONLY activities for the city '{city}'. If there are times, respect them; if not, infer shifts (morning/midday/afternoon/evening)."
            )

            resp = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.2,
                max_tokens=700
            )
            content = resp.choices[0].message.content or "{}"
            import json, re
            cleaned = re.sub(r"```[a-zA-Z]*", "", content).replace("```", "").strip()
            data = json.loads(cleaned)
            items = data.get("items", [])
            # Minimal normalization
            out: List[Dict[str, Any]] = []
            for it in items:
                name = it.get("place_name") or it.get("name") or "Activity"
                time_val = it.get("time") or ""
                cat = it.get("category") or "visit"
                dur = it.get("duration_min")
                out.append({
                    "time": time_val,
                    "place_name": name,
                    "category": cat,
                    "duration_min": dur
                })
            return out
        except Exception as e:
            logger.warning(f"_extract_city_items_from_itinerary_text error: {e}")
            return []

    def _map_items_to_candidates(self, items: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assigns place_id/coords to items trying to match by similarity with candidates. Returns normalized items.
        """
        def similarity(a: str, b: str) -> float:
            return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

        mapped: List[Dict[str, Any]] = []
        for it in items:
            name = it.get("place_name") or ""
            best = None
            best_score = 0.0
            for c in candidates:
                score = similarity(name, c.get("name", ""))
                if score > best_score:
                    best = c
                    best_score = score
            if best is not None and best_score >= 0.72:  # reasonable threshold
                mapped.append({
                    "time": it.get("time"),
                    "place_id": best.get("id"),
                    "place_name": best.get("name") or name,
                    "category": it.get("category") or best.get("category") or "visit",
                    "coordinates": best.get("coordinates"),
                    "duration_min": it.get("duration_min")
                })
            else:
                # Keep as string without ID if no match
                mapped.append({
                    "time": it.get("time"),
                    "place_id": None,
                    "place_name": name,
                    "category": it.get("category") or "visit",
                    "coordinates": None,
                    "duration_min": it.get("duration_min")
                })
        return mapped

    def _generate_day_with_llm(self, city: str, window: Dict[str, str], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Uses LLM to propose a list of visits with times. Doesn't require linking to DB; if there are candidates, they are suggested by name.
        Returns list of dicts with keys: time, place_name, category, coordinates?, duration_min?
        """
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )

            sites_brief = [
                {
                    "name": c.get("name"),
                    "category": c.get("category"),
                    "coordinates": c.get("coordinates")
                }
                for c in candidates[:12]
            ]

            prompt = {
                "city": city,
                "window": window,
                "candidates": sites_brief,
            }

            system = (
                "You are a visit planner. Return ONLY JSON with an 'items' array\n"
                "Each item: {time:'HH:MM', place_name:string, category?:string, duration_min?:number}.\n"
                "Don't invent ids or HTML. If there are no candidates, create generic names."
            )

            resp = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Generate visits for {city} from {window['start']} to {window['end']}. Candidates: {sites_brief}"}
                ],
                temperature=0.2,
                max_tokens=500
            )
            content = resp.choices[0].message.content or "{}"
            import json, re
            cleaned = re.sub(r"```[a-zA-Z]*", "", content).replace("```", "").strip()
            data = json.loads(cleaned)
            items = data.get("items", [])
            # Normalize coordinates if they come
            for it in items:
                coords = it.get("coordinates")
                if isinstance(coords, dict):
                    lat = coords.get("latitude") or coords.get("lat")
                    lon = coords.get("longitude") or coords.get("lon")
                    try:
                        it["coordinates"] = {"latitude": float(lat), "longitude": float(lon)} if lat is not None and lon is not None else None
                    except Exception:
                        it["coordinates"] = None
            return items
        except Exception as e:
            logger.warning(f"LLM generation error: {e}")
            return []


daily_visits_service = DailyVisitsService()


