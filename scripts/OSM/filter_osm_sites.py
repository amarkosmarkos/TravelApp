#!/usr/bin/env python3
"""
Script para procesar datos de OpenStreetMap y extraer sitios turísticos,
con capacidad de reanudar a partir del último progreso guardado.
"""

import osmium
import json
from pathlib import Path

# Configuración de rutas
OSM_FILE = Path(r"D:\TravelApp\OSM\planet-250609.osm.pbf")
SCRIPT_DIR = Path(__file__).parent
# Carpeta de datos: Project/scripts/data/OSM
DATA_DIR = SCRIPT_DIR.parent / "data" / "OSM"
# Crear toda la jerarquía si hace falta
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "sites_filtered.jsonl"
PROGRESS_FILE = DATA_DIR / "progress.json"

# Constantes
INTERESTING_KEYS = {"tourism", "amenity", "historic", "leisure",
                    "natural", "man_made", "shop"}
USEFUL_TAGS = {
    "name", "alt_name", "name:en", "name:es", "wikidata", "wikipedia",
    "description", "short_description", "image", "opening_hours",
    "website", "email", "phone", "addr:street", "addr:city",
    "addr:country", "addr:postcode"
}
SAVE_EVERY = 100_000  # Guarda progreso cada 100k elementos

class TourismHandler(osmium.SimpleHandler):
    def __init__(self, resume_count, total_estimated):
        super().__init__()
        self.processed_count = resume_count
        self.interesting_count = 0
        self.resume_count = resume_count
        self.total_estimated = total_estimated
        self.buffer = []

    def save_progress(self):
        data = {
            "processed_count": self.processed_count,
            "interesting_count": self.interesting_count,
            "output_file_size": OUTPUT_FILE.stat().st_size if OUTPUT_FILE.exists() else 0
        }
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def flush_buffer(self):
        if not self.buffer:
            return
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for item in self.buffer:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"💾 Guardados {len(self.buffer):,} sitios relevantes")
        self.buffer.clear()
        self.save_progress()

    def process(self, obj, obj_type):
        self.processed_count += 1
        if self.processed_count <= self.resume_count:
            return
        if self.processed_count % SAVE_EVERY == 0:
            pct = (self.processed_count / self.total_estimated) * 100
            print(f"Procesados {self.processed_count:,} (~{pct:.2f}%)")

        tags = dict(obj.tags)
        if any(k in tags for k in INTERESTING_KEYS):
            self.interesting_count += 1
            record = {
                "_id": f"osm_{obj_type}_{obj.id}",
                "osm_type": obj_type,
                "osm_id": obj.id,
                "useful_tags": {},
                "other_tags": {}
            }
            if obj_type == "node":
                record["location"] = {"lat": obj.location.lat, "lon": obj.location.lon}
            else:
                record["location"] = {}
            for k, v in tags.items():
                (record["useful_tags"] if k in USEFUL_TAGS else record["other_tags"]).setdefault(k, v)
            self.buffer.append(record)
            if len(self.buffer) >= SAVE_EVERY:
                self.flush_buffer()

    def node(self, n): self.process(n, "node")
    def way(self, w): self.process(w, "way")
    def relation(self, r): self.process(r, "relation")


def estimate_total(file_bytes):
    avg = 200
    return max(1, file_bytes // avg)


def main():
    print(f"📁 Archivo OSM: {OSM_FILE}")
    if not OSM_FILE.exists():
        print("❌ Archivo OSM no encontrado.")
        return
    size = OSM_FILE.stat().st_size
    total_est = estimate_total(size)
    print(f"📦 Tamaño: {size / (1024**3):.2f} GB")
    print(f"📊 Estimado ~{total_est:,} elementos")

    resume = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            resume = json.load(f).get("processed_count", 0)
        print(f"🔄 Reanudando desde {resume:,} elementos")
    else:
        print("▶️ Comenzando desde cero")

    handler = TourismHandler(resume_count=resume, total_estimated=total_est)

    reader = osmium.io.Reader(
        str(OSM_FILE),
        osmium.osm.osm_entity_bits.NODE |
        osmium.osm.osm_entity_bits.WAY |
        osmium.osm.osm_entity_bits.RELATION
    )
    print("🚀 Iniciando procesamiento...")
    osmium.apply(reader, handler)
    reader.close()

    handler.flush_buffer()
    print(f"\n✅ Completado. Procesados: {handler.processed_count:,}, Relevantes: {handler.interesting_count:,}")

if __name__ == "__main__":
    main()
