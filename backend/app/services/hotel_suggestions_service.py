from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from app.database import get_itineraries_collection
from app.config import settings

logger = logging.getLogger(__name__)


class HotelSuggestionsService:
    """
    Sugerencias de hoteles por ciudad basadas en el itinerario.
    - Obtiene ciudades y fechas (check-in/check-out) del itinerario por travel_id
    - Usa LLM para proponer 3–5 hoteles por ciudad (solo strings)
    - Enriquecemos con imagen de Wikimedia cuando sea posible
    - Generamos deeplinks a Booking con fechas para que el usuario vea disponibilidad real
    """

    def __init__(self) -> None:
        # Cache simple en memoria con TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds: int = 6 * 3600
        # Limitar concurrencia (por cortesía de APIs públicas)
        self._city_sem = asyncio.Semaphore(3)
        self._img_sem = asyncio.Semaphore(5)

    async def get_suggestions_for_travel(self, travel_id: str) -> List[Dict[str, Any]]:
        itineraries = await get_itineraries_collection()
        itinerary = await itineraries.find_one({"travel_id": travel_id})
        if not itinerary:
            logger.warning(f"Itinerary not found for travel_id={travel_id}")
            return []

        cities = itinerary.get("cities") or []
        tasks = []
        for city in cities:
            city_name = city.get("name") or city.get("city_name") or ""
            if not city_name:
                continue
            tasks.append(self._build_city_suggestions(travel_id, city))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, dict):
                out.append(r)
            else:
                logger.warning(f"City suggestion task returned exception: {r}")
        return out

    async def generate_and_save_for_travel(self, travel_id: str) -> bool:
        """
        Genera sugerencias y las guarda embebidas en el documento del itinerario
        para respuesta instantánea en el endpoint y para frontend.
        """
        try:
            suggestions = await self.get_suggestions_for_travel(travel_id)
            itineraries = await get_itineraries_collection()
            await itineraries.update_one(
                {"travel_id": travel_id},
                {"$set": {
                    "hotel_suggestions": suggestions,
                    "hotel_suggestions_generated_at": datetime.utcnow().isoformat()
                }}
            )
            return True
        except Exception as e:
            logger.error(f"Error generating and saving hotel suggestions: {e}")
            return False

    async def _build_city_suggestions(self, travel_id: str, city: Dict[str, Any]) -> Dict[str, Any]:
        city_name = city.get("name") or city.get("city_name") or ""
        check_in, check_out = self._infer_dates_for_city(city)
        nights = self._calc_nights(check_in, check_out)

        cache_key = f"{travel_id}:{city_name}:{check_in}:{check_out}"
        now = datetime.utcnow().timestamp()
        cached = self._cache.get(cache_key)
        if cached and (now - cached.get("ts", 0)) < self._cache_ttl_seconds:
            return cached["value"]

        async with self._city_sem:
            try:
                hotels = await self._llm_hotels_for_city(city_name, nights)
            except Exception as e:
                logger.error(f"LLM hotels error for {city_name}: {e}")
                hotels = []

        async def _enrich(h: Dict[str, Any]) -> Dict[str, Any]:
            name = h.get("name") or "Hotel"
            image_url = None
            async with self._img_sem:
                image_url = await self._wikimedia_image_for_query(f"{name} {city_name}")
            deeplink = self._build_booking_deeplink(name, city_name, check_in, check_out)
            return {
                "city": city_name,
                "name": name,
                "area": h.get("area"),
                "price_tier": h.get("price_tier"),
                "notes": h.get("notes"),
                "image_url": image_url,
                "deeplink_url": deeplink,
                "check_in": check_in,
                "check_out": check_out,
                "nights": nights,
            }

        enriched_list = await asyncio.gather(*[ _enrich(h) for h in hotels ], return_exceptions=False)

        # Generar días individuales
        days_array: List[Dict[str, Any]] = []
        try:
            ci = datetime.fromisoformat(check_in)
            co = datetime.fromisoformat(check_out)
            d = ci
            while d < co:
                days_array.append({
                    "date": d.date().isoformat(),
                    "hotels": enriched_list
                })
                d = d + timedelta(days=1)
        except Exception:
            days_array.append({"date": check_in, "hotels": enriched_list})

        value = {
            "city": city_name,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "days": days_array,
            "hotels": enriched_list,
        }
        self._cache[cache_key] = {"ts": now, "value": value}
        return value

    def _infer_dates_for_city(self, city: Dict[str, Any]) -> tuple[str, str]:
        check_in = None
        check_out = None
        try:
            arr = city.get("arrival_dt")
            dep = city.get("departure_dt")
            if arr:
                arr_dt = datetime.fromisoformat(str(arr).replace("Z", "+00:00"))
                check_in = arr_dt.date().isoformat()
            if dep:
                dep_dt = datetime.fromisoformat(str(dep).replace("Z", "+00:00"))
                check_out = dep_dt.date().isoformat()
        except Exception:
            pass
        if not check_in:
            check_in = datetime.utcnow().date().isoformat()
        if not check_out:
            # Por defecto +2 días desde check_in
            base_dt = datetime.fromisoformat(check_in) if isinstance(check_in, str) else datetime.utcnow()
            check_out = (base_dt + timedelta(days=2)).date().isoformat()
        return check_in, check_out

    def _calc_nights(self, check_in: str, check_out: str) -> int:
        try:
            ci = datetime.fromisoformat(check_in)
            co = datetime.fromisoformat(check_out)
            d = (co - ci).days
            return max(1, d)
        except Exception:
            return 1

    async def _llm_hotels_for_city(self, city: str, nights: int) -> List[Dict[str, Any]]:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=(settings.AZURE_OPENAI_ENDPOINT if str(settings.AZURE_OPENAI_ENDPOINT).startswith("http") else f"https://{settings.AZURE_OPENAI_ENDPOINT}")
        )
        system = (
            "Eres un experto en hoteles. Devuelve SOLO JSON válido con key 'hotels' (3-5 items).\n"
            "Cada hotel: {name, area?:string, price_tier?:'budget'|'mid'|'premium', notes?:string}."
        )
        user = (
            f"Ciudad: {city}\n"
            f"Noches: {nights}\n"
            "Sugiere 3-5 hoteles conocidos/populares con variedad de precio y zonas."
        )
        resp = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.2,
            max_tokens=600
        )
        content = resp.choices[0].message.content or "{}"
        cleaned = content.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            return data.get("hotels", [])
        except Exception:
            logger.warning("Failed to parse hotels JSON from LLM")
            return []

    async def _wikimedia_image_for_query(self, query: str) -> Optional[str]:
        try:
            # Buscar página relacionada
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "srprop": ""
            }
            search = await self._fetch_json("https://en.wikipedia.org/w/api.php", search_params)
            hits = (search.get("query", {}).get("search", []) or [])
            if not hits:
                return None
            page_title = hits[0].get("title")

            # Obtener thumbnail
            image_params = {
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "piprop": "thumbnail",
                "pithumbsize": 640,
                "titles": page_title
            }
            img = await self._fetch_json("https://en.wikipedia.org/w/api.php", image_params)
            pages = img.get("query", {}).get("pages", {})
            for _, page in pages.items():
                thumb = page.get("thumbnail")
                if thumb and thumb.get("source"):
                    return thumb.get("source")
            return None
        except Exception as e:
            logger.warning(f"Wikimedia image lookup failed for '{query}': {e}")
            return None

    async def _fetch_json(self, base_url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        def _do_request() -> Dict[str, Any]:
            qs = urlencode(params, doseq=True)
            url = f"{base_url}?{qs}"
            req = Request(url, headers={"User-Agent": "TravelApp/1.0 (+https://example.com)"})
            with urlopen(req, timeout=8) as resp:
                data = resp.read().decode("utf-8", errors="ignore")
                return json.loads(data)
        return await asyncio.to_thread(_do_request)

    def _build_booking_deeplink(self, hotel_name: str, city: str, check_in: str, check_out: str) -> str:
        try:
            query = f"{hotel_name} {city}".strip()
            params = {
                "ss": query,
                "checkin": check_in,
                "checkout": check_out,
                "group_adults": 2,
                "no_rooms": 1,
                "group_children": 0,
            }
            return f"https://www.booking.com/search.html?{urlencode(params)}"
        except Exception:
            # Fallback mínimo
            safe_query = urlencode({"q": f"{hotel_name} {city}"})
            return f"https://www.google.com/search?{safe_query}"


hotel_suggestions_service = HotelSuggestionsService()


