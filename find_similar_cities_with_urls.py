from difflib import SequenceMatcher
from itertools import combinations
import json
from collections import defaultdict

def similarity(a, b):
    """Calcula la similitud entre dos strings (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def load_entities_from_jsonl(file_path):
    """Carga las entidades desde el archivo JSONL y las agrupa por tipo"""
    entidades_por_tipo = defaultdict(list)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                url = data.get('url', 'URL desconocida')
                source_name = data.get('source_name', 'Fuente desconocida')
                
                # Agregar información de origen a cada entidad
                for entidad in data.get('entities', []):
                    entidad['source_url'] = url
                    entidad['source_name'] = source_name
                    
                    tipo = entidad.get('entity_type', 'desconocido')
                    if isinstance(tipo, list):
                        tipo = tipo[0] if tipo else 'desconocido'
                    elif tipo is None:
                        tipo = 'desconocido'
                    
                    entidades_por_tipo[tipo].append(entidad)
    
    return entidades_por_tipo

def find_similar_cities_with_urls(entidades_por_tipo, threshold=0.7):
    """Encuentra ciudades similares y las agrupa, mostrando las URLs de origen"""
    ciudades = entidades_por_tipo.get('site', [])
    
    if not ciudades:
        print("No se encontraron ciudades")
        return
    
    # Extraer nombres de ciudades con información de origen
    ciudades_con_origen = []
    for ciudad in ciudades:
        nombre = ciudad.get('name') or ciudad.get('title') or ciudad.get('advice_text') or '[Sin nombre]'
        if nombre and nombre != '[Sin nombre]':
            ciudades_con_origen.append({
                'nombre': nombre,
                'url': ciudad.get('source_url', 'URL desconocida'),
                'source_name': ciudad.get('source_name', 'Fuente desconocida')
            })
    
    # Encontrar grupos de ciudades similares
    grupos_similares = []
    ciudades_usadas = set()
    
    for i, ciudad1 in enumerate(ciudades_con_origen):
        if ciudad1['nombre'] in ciudades_usadas:
            continue
            
        grupo = [ciudad1]
        ciudades_usadas.add(ciudad1['nombre'])
        
        # Buscar ciudades similares
        for ciudad2 in ciudades_con_origen[i+1:]:
            if ciudad2['nombre'] not in ciudades_usadas:
                sim = similarity(ciudad1['nombre'], ciudad2['nombre'])
                if sim >= threshold:
                    grupo.append(ciudad2)
                    ciudades_usadas.add(ciudad2['nombre'])
        
        if len(grupo) > 1:  # Solo grupos con más de una ciudad
            grupos_similares.append(grupo)
    
    # Mostrar resultados ordenados alfabéticamente
    print(f"=== CIUDADES SIMILARES (similitud >= {threshold}) ===")
    print(f"Total de ciudades: {len(ciudades_con_origen)}")
    print(f"Grupos de ciudades similares: {len(grupos_similares)}")
    
    # Mostrar grupos ordenados alfabéticamente
    for grupo in sorted(grupos_similares, key=lambda x: x[0]['nombre'].lower()):
        print(f"\n📍 {grupo[0]['nombre']} (principal):")
        for ciudad in grupo[1:]:
            sim = similarity(grupo[0]['nombre'], ciudad['nombre'])
            print(f"   └─ {ciudad['nombre']} (similitud: {sim:.2f})")
            print(f"      📍 URL: {ciudad['url']}")
            print(f"      📰 Fuente: {ciudad['source_name']}")
    
    # Mostrar ciudades únicas (sin similares)
    ciudades_unicas = [c for c in ciudades_con_origen if c['nombre'] not in ciudades_usadas or 
                      not any(c['nombre'] in [ciudad['nombre'] for ciudad in grupo] for grupo in grupos_similares if len(grupo) > 1)]
    
    if ciudades_unicas:
        print(f"\n🏙️  CIUDADES ÚNICAS ({len(ciudades_unicas)}):")
        for ciudad in sorted(ciudades_unicas, key=lambda x: x['nombre'].lower()):
            print(f"   • {ciudad['nombre']}")
            print(f"     📍 URL: {ciudad['url']}")
            print(f"     📰 Fuente: {ciudad['source_name']}")

# Ejemplo de uso
if __name__ == "__main__":
    # Cargar datos desde el archivo JSONL
    file_path = "scripts/data/scraper_enrichment/enriched_data.jsonl"
    entidades_por_tipo = load_entities_from_jsonl(file_path)
    
    # Ejecutar la función
    find_similar_cities_with_urls(entidades_por_tipo, threshold=0.85) 