import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener API key desde variable de entorno
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise ValueError("SERPAPI_KEY no encontrada en el archivo .env")

search_queries = [
    "qué ver en Tailandia",
    "guía de viaje Tailandia"]

def load_existing_urls():
    existing_urls = set()
    try:
        with open("urls_list.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                if "url" in data:
                    existing_urls.add(data["url"])
    except FileNotFoundError:
        pass
    return existing_urls

def buscar_urls(query):
    params = {
        "engine": "google",
        "q": query,
        "hl": "es",
        "num": 25,
        "api_key": SERPAPI_KEY
    }
    r = requests.get("https://serpapi.com/search", params=params)
    resultados = r.json()
    urls = [item["link"] for item in resultados.get("organic_results", [])]
    return urls

# Cargar URLs existentes
existing_urls = load_existing_urls()
print(f"URLs existentes: {len(existing_urls)}")

# Buscar y añadir nuevas URLs
with open("urls_list.jsonl", "a", encoding="utf-8") as f:
    for query in search_queries:
        urls = buscar_urls(query)
        for url in urls:
            if url not in existing_urls:
                f.write(json.dumps({"query": query, "url": url}) + "\n")
                existing_urls.add(url)
                print(f"Añadida: {url}")

print("¡Listo!") 