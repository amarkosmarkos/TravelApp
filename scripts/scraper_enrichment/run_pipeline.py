import os
import json
from pathlib import Path
from extractor.download_page import download_and_clean
from extractor.text_chunker import chunk_text
from extractor.llm_extractor import extract_entities

CONFIG_PATH = Path(__file__).parent / 'config.json'
URLS_PATH = Path(__file__).parent / 'urls_list.jsonl'
OUTPUT_PATH = Path(r'D:/TravelApp/Project/scripts/data/scraper_enrichment/enriched_data.jsonl')
OUTPUT_DIR = r'D:/TravelApp/Project/scripts/data/scraper_enrichment'


def load_config():
    # Configuración sigue en JSON normal
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_source_name(url):
    from urllib.parse import urlparse
    return urlparse(url).netloc

def load_existing_results():
    """Carga las entradas existentes en el archivo JSONL de salida y las devuelve como un dict por URL."""
    results = {}
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        url = data.get('url')
                        if url:
                            results[url] = data
                    except Exception:
                        continue
    return results

def main():
    config = load_config()
    # Leer URLs desde un archivo JSONL (una URL por línea)
    with open(URLS_PATH, 'r', encoding='utf-8') as f:
        urls = [json.loads(line)['url'] if 'url' in json.loads(line) else line.strip() for line in f if line.strip()]
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    # Cargar resultados existentes para poder reemplazar por URL
    existing_results = load_existing_results()
    for url in urls:
        print(f'Procesando: {url}')
        try:
            text = download_and_clean(url)
            chunks = chunk_text(text, config.get('chunk_size_tokens', 1200), config.get('chunk_overlap', 50), "gpt-35-turbo")
            all_entities = []
            for chunk in chunks:
                enriched = extract_entities(chunk, config, url, get_source_name(url))
                all_entities.extend(enriched['entities'])
            
            result = {
                'url': url,
                'source_name': get_source_name(url),
                'scraped_at': enriched['scraped_at'],
                'entities': all_entities  # Guardar todas las entidades, incluyendo duplicados
            }
            # Reemplazar (o añadir) la entrada para esta URL
            existing_results[url] = result
        except Exception as e:
            print(f'Error procesando {url}: {e}')
    # Sobrescribir el archivo con una sola entrada por URL (la más reciente)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as out_f:
        for data in existing_results.values():
            out_f.write(json.dumps(data, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    main() 