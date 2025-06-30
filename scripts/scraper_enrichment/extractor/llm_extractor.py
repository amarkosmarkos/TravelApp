import os
import sys
from pathlib import Path
import json
from datetime import datetime
import difflib
import unicodedata

# Eliminar cualquier variable de entorno de proxy antes de cualquier import de openai
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(var, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# Añadir la carpeta 'backend' al sys.path para que 'app' sea importable
sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))
from app.config.settings import settings

# Define el schema de la función para function calling
entity_schema = {
  "name": "extract_travel_entities",
  "description": "Extract travel entities from text; each entity_type branch has only its relevant fields.",
  "parameters": {
    "type": "object",
    "properties": {
      "entities": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["entity_type", "name"],
          "oneOf": [
            {
              "title": "Site / POI",
              "properties": {
                "entity_type": { "const": "site" },
                "name": { "type": "string" },
                "subtype": {
                  "type": "string",
                  "description": "e.g. museum, temple, waterfall, beach, city, island, province, state, country"
                },
                "description": { "type": "string" },
                "hierarchy": {
                  "type": "array",
                  "description": "Ordered list of higher-order places (e.g., city, province, state, country, island).",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": { "type": "string" },
                      "name": { "type": "string" },
                      "region": { "type": "string" },
                      "code": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 for country, if applicable"
                      }
                    },
                    "required": ["type", "name"]
                  }
                },
                "location_text": { "type": "string" },
                "lat": { "type": ["number", "null"] },
                "lon": { "type": ["number", "null"] },
                "price": { "type": "string" },
                "currency": { "type": "string" },
                "hours": { "type": "string" },
                "avg_visit_duration": { "type": "string" },
                "security": { "type": "string" },
                "restrictions": {
                  "type": "object",
                  "properties": {
                    "age": { "type": "string" },
                    "clothing": { "type": "string" },
                    "accessibility": { "type": "string" },
                    "gender": { "type": "string" },
                    "other": { "type": "string" }
                  }
                },
                "user_impressions": {
                  "type": "object",
                  "properties": {
                    "liked": { "type": ["boolean", "null"] },
                    "must_see": { "type": ["boolean", "null"] },
                    "emotions": { "type": "string" }
                  }
                },
                "nearby_suggestions": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "official_website": { "type": "string" },
                "images": {
                  "type": "array",
                  "items": { "type": "string" }
                }
              }
            },
            {
              "title": "Transport",
              "properties": {
                "entity_type": { "const": "transport" },
                "name": { "type": "string" },
                "transport_mode": {
                  "type": "string",
                  "description": "e.g. bus, train, flight, ferry, private car"
                },
                "origin_site": { "type": "string", "description": "Name of origin site (must match a 'site' entity)" },
                "destination_site": { "type": "string", "description": "Name of destination site (must match a 'site' entity)" },
                "origin_station": { "type": ["string", "null"], "description": "Station or terminal at origin, if applicable" },
                "destination_station": { "type": ["string", "null"], "description": "Station or terminal at destination, if applicable" },
                "duration": { "type": "string", "description": "e.g. '3h 20m'" },
                "price": { "type": "string" },
                "currency": { "type": "string" }
              },
              "required": ["origin_site", "destination_site"]
            },
            {
              "title": "Itinerary",
              "properties": {
                "entity_type": { "const": "itinerary" },
                "title": { "type": "string" },
                "description": { "type": "string" },
                "duration": { "type": "string" },
                "sites_visited": {
                  "type": "array",
                  "items": { "type": "string" },
                  "description": "List of site names visited"
                },
                "day_by_day_plan": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["day", "activities"],
                    "properties": {
                      "day": { "type": "integer" },
                      "activities": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "required": ["site", "description"],
                          "properties": {
                            "site": { "type": "string", "description": "Name of site visited" },
                            "description": { "type": "string" },
                            "start_time": { "type": "string" },
                            "end_time": { "type": "string" }
                          }
                        }
                      }
                    }
                  }
                },
                "transportation_tips": { "type": "string" }
              },
              "required": ["day_by_day_plan"]
            },
            {
              "title": "Tip",
              "properties": {
                "entity_type": { "const": "tip" },
                "advice_text": { "type": "string" },
                "context": { "type": "string" }
              },
              "required": ["advice_text"]
            },
            {
              "title": "Activity",
              "properties": {
                "entity_type": { "const": "activity" },
                "name": { "type": "string" },
                "description": { "type": "string" },
                "site": { "type": "string", "description": "Name of site where activity occurs" },
                "start_time": { "type": "string" },
                "end_time": { "type": "string" },
                "price": { "type": "string" },
                "currency": { "type": "string" }
              }
            },
            {
              "title": "Event or Festival",
              "properties": {
                "entity_type": { "enum": ["event", "festival"] },
                "name": { "type": "string" },
                "type": { "type": "string" },
                "description": { "type": "string" },
                "site": { "type": "string", "description": "Name of site where event occurs" },
                "start_date": { "type": "string", "format": "date" },
                "end_date": { "type": "string", "format": "date" },
                "price": { "type": "string" },
                "currency": { "type": "string" },
                "official_website": { "type": "string" },
                "images": { "type": "array", "items": { "type": "string" } }
              }
            }
          ]
        }
      }
    },
    "required": ["entities"]
  }
}



def normalize_name(name):
    name = name.lower()
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    
    name = ' '.join(name.split())
    return name

def deduplicate_entities(entities, entity_types=("city", "site", "hotel"), name_field='name'):
    """
    Devuelve (entidades_sin_duplicados, duplicados_log)
    """
    seen = {}
    duplicates_log = []
    result = []
    for ent in entities:
        if ent.get('entity_type') in entity_types and ent.get(name_field):
            norm_name = normalize_name(ent[name_field])
            if norm_name in seen:
                prev = seen[norm_name]
                duplicates_log.append({
                    'entity_type': ent['entity_type'],
                    'original_names': [prev[name_field], ent[name_field]],
                    'normalized': norm_name
                })
                for k, v in ent.items():
                    if v and v != prev.get(k):
                        if not prev.get(k):
                            prev[k] = v
                        elif isinstance(prev[k], list) and isinstance(v, list):
                            # Deduplicar listas, permitiendo elementos no hashables
                            combined = prev[k] + v
                            deduped = []
                            seen_items = set()
                            for item in combined:
                                try:
                                    key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, dict) else str(item)
                                except Exception:
                                    key = str(item)
                                if key not in seen_items:
                                    seen_items.add(key)
                                    deduped.append(item)
                            prev[k] = deduped
                        elif prev[k] != v:
                            # Si alguno es lista, combínalos y deduplica
                            if isinstance(prev[k], list):
                                combined = prev[k] + ([v] if not isinstance(v, list) else v)
                            elif isinstance(v, list):
                                combined = ([prev[k]] if not isinstance(prev[k], list) else prev[k]) + v
                            else:
                                combined = [prev[k], v]
                            deduped = []
                            seen_items = set()
                            for item in combined:
                                try:
                                    key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, dict) else str(item)
                                except Exception:
                                    key = str(item)
                                if key not in seen_items:
                                    seen_items.add(key)
                                    deduped.append(item)
                            prev[k] = deduped
            else:
                seen[norm_name] = ent
        else:
            result.append(ent)
    result.extend(seen.values())
    return result, duplicates_log

def save_entities_and_log(url, entities_with_dupes, entities_no_dupes, duplicates_log, output_dir):
    # Guardar entidades (con duplicados, ya que la eliminación será manual)
    with open(Path(output_dir) / "entities_with_duplicates.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"url": url, "entities": entities_with_dupes}, ensure_ascii=False) + "\n")
    # También guardar en el archivo sin duplicados (mismo contenido por ahora)
    with open(Path(output_dir) / "entities_no_duplicates.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"url": url, "entities": entities_no_dupes}, ensure_ascii=False) + "\n")
    # El log de duplicados estará vacío ya que la eliminación será manual
    with open(Path(output_dir) / "merged_entities.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"url": url, "merged": duplicates_log}, ensure_ascii=False) + "\n")

def similar(a, b, threshold=0.85):
    """Devuelve True si los nombres son suficientemente similares."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold

def extract_entities(chunk, config, url, source_name):
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    )
    prompt = f"""
Extract structured travel entities from the following text according to the provided JSON schema. The result should be an array of entities, following the detailed format and fields. If there is no information for a field, leave it empty or null.

DO NOT repeat entities: if an entity appears multiple times in the text, group all information in a single object.

All text must be in ENGLISH. Country field must be ISO 3166-1 alpha-2 country code (e.g., 'TH' for Thailand, 'ES' for Spain).

In the 'day_by_day_plan' field of itineraries, each element should be an object with fields: 'day' (number), 'activities' (array with city, place, description, start_time, end_time).

TEXT:
{chunk}
"""
    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Eres un extractor de información de viajes."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.2,
        tools=[{"type": "function", "function": entity_schema}],
        tool_choice={"type": "function", "function": {"name": "extract_travel_entities"}}
    )
    tool_call = response.choices[0].message.tool_calls[0]
    function_args = json.loads(tool_call.function.arguments)
    entities = function_args["entities"]
    return {
        "url": url,
        "source_name": source_name,
        "scraped_at": datetime.utcnow().isoformat(),
        "entities": entities
    } 