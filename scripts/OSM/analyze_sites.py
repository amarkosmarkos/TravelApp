#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter, defaultdict

# Configuración de rutas
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
SITES_FILE = DATA_DIR / "sites_filtered.jsonl"

def analyze_sites():
    print("=== ANÁLISIS STREAMING DE SITIOS TURÍSTICOS ===")
    print(f"Archivo: {SITES_FILE}\n")

    if not SITES_FILE.exists():
        print(f"❌ Error: {SITES_FILE} no existe.")
        return

    # Contadores y estructuras
    total = 0
    osm_types = Counter()
    countries = Counter()
    cities = Counter()

    tourism_tags = Counter()
    amenity_tags = Counter()
    historic_tags = Counter()
    leisure_tags = Counter()
    natural_tags = Counter()
    man_made_tags = Counter()
    shop_tags = Counter()

    sites_with = {
        "name": 0,
        "website": 0,
        "phone": 0,
        "opening_hours": 0,
        "wikidata": 0,
        "location": 0,
    }

    examples = {
        "hotels": [],
        "museums": [],
        "restaurants": [],
    }

    # Procesamiento streaming
    with SITES_FILE.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if i % 1_000_000 == 0:
                print(f"🔄 Procesadas {i:,} líneas...")

            try:
                site = json.loads(line)
            except json.JSONDecodeError:
                continue

            total += 1
            t = site.get("osm_type")
            osm_types[t] += 1

            tags = site.get("useful_tags", {})
            # País y ciudad
            c = tags.get("addr:country")
            if c: countries[c] += 1
            city = tags.get("addr:city")
            if city: cities[city] += 1

            # Tags de interés
            if "tourism" in tags:
                tourism_tags[tags["tourism"]] += 1
            if "amenity" in tags:
                amenity_tags[tags["amenity"]] += 1
            if "historic" in tags:
                historic_tags[tags["historic"]] += 1
            if "leisure" in tags:
                leisure_tags[tags["leisure"]] += 1
            if "natural" in tags:
                natural_tags[tags["natural"]] += 1
            if "man_made" in tags:
                man_made_tags[tags["man_made"]] += 1
            if "shop" in tags:
                shop_tags[tags["shop"]] += 1

            # Información adicional
            if "name" in site.get("useful_tags", {}):
                sites_with["name"] += 1
            if "website" in site.get("useful_tags", {}):
                sites_with["website"] += 1
            if "phone" in site.get("useful_tags", {}):
                sites_with["phone"] += 1
            if "opening_hours" in site.get("useful_tags", {}):
                sites_with["opening_hours"] += 1
            if "wikidata" in site.get("useful_tags", {}):
                sites_with["wikidata"] += 1
            if site.get("location"):
                sites_with["location"] += 1

            # Ejemplos
            if tags.get("tourism") == "hotel" and len(examples["hotels"]) < 3:
                examples["hotels"].append((site.get("useful_tags").get("name","?"),
                                           tags.get("website", "?")))
            if tags.get("tourism") == "museum" and len(examples["museums"]) < 3:
                examples["museums"].append((site.get("useful_tags").get("name","?"),
                                            tags.get("wikidata", "?")))
            if tags.get("amenity") == "restaurant" and len(examples["restaurants"]) < 3:
                examples["restaurants"].append((site.get("useful_tags").get("name","?"),
                                                tags.get("opening_hours", "?")))

    # Resultados finales
    print("\n✅ Procesado completo")
    print(f"Total de sitios: {total:,}\n")

    def show_counter(title, counter, top=10):
        print(f"{title}:")
        for k, v in counter.most_common(top):
            print(f"  - {k}: {v:,}")
        print()

    show_counter("Distribución por tipo OSM", osm_types)
    show_counter("Top 10 países", countries)
    show_counter("Top 10 ciudades", cities)
    show_counter("Top 10 tourism", tourism_tags)
    show_counter("Top 10 amenity", amenity_tags)
    show_counter("Top 10 historic", historic_tags)
    show_counter("Top 10 leisure", leisure_tags)
    show_counter("Top 10 natural", natural_tags)
    show_counter("Top 10 man_made", man_made_tags)
    show_counter("Top 10 shop", shop_tags)

    print("Información adicional:")
    for field, cnt in sites_with.items():
        pct = cnt/total*100 if total else 0
        print(f"  - Con {field}: {cnt:,} ({pct:.1f}%)")
    print()

    print("Ejemplos:")
    for category, items in examples.items():
        print(f" {category.capitalize()}:")
        for name, extra in items:
            print(f"   - {name} → {extra}")
    print()

def main():
    analyze_sites()

if __name__ == "__main__":
    main()
