import json
import time
import requests
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict

def get_quality_level(importance_score):
    """Determina el nivel de calidad basado en el score de importancia"""
    if importance_score >= 0.9:
        return "excellent"
    elif importance_score >= 0.7:
        return "good"
    elif importance_score >= 0.5:
        return "fair"
    else:
        return "poor"

def search_nominatim(query, max_retries=3):
    """Busca en Nominatim con rate limiting y reintentos"""
    base_url = "https://nominatim.openstreetmap.org/search"
    
    for attempt in range(max_retries):
        try:
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            headers = {
                'User-Agent': 'TravelApp/1.0 (https://github.com/travelapp)'
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            if results:
                return results[0]
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error en intento {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial
            else:
                return None
    
    return None

def extract_wikipedia_info(nominatim_result):
    """Extrae información de Wikipedia del resultado de Nominatim"""
    wikipedia_info = {}
    
    # Extraer Wikipedia ID
    wikipedia = nominatim_result.get('wikipedia', '')
    if wikipedia:
        wikipedia_info['wikipedia_id'] = wikipedia
        # Crear URL de Wikipedia
        lang, title = wikipedia.split(':', 1) if ':' in wikipedia else ('en', wikipedia)
        wikipedia_info['wikipedia_url'] = f"https://{lang}.wikipedia.org/wiki/{quote(title)}"
    
    return wikipedia_info

def create_search_queries(site_data):
    """Crea diferentes consultas de búsqueda para un sitio"""
    name = site_data.get('name', '').strip()
    
    # Extraer ciudad
    city = site_data.get('city', '').strip()
    if not city and site_data.get('subtype') == 'city':
        city = name  # Si es una ciudad, usar el nombre como ciudad
    
    # Extraer país de hierarchy
    country = ''
    hierarchy = site_data.get('hierarchy', [])
    for item in hierarchy:
        if item.get('type') == 'country':
            country = item.get('name', '').strip()
            break
    
    # Fallback: usar location_text si no hay país
    if not country:
        location_text = site_data.get('location_text', '').strip()
        if location_text and 'Thailand' in location_text:
            country = 'Thailand'
    
    queries = []
    
    # Query 1: nombre + ciudad + país
    if name and city and country:
        queries.append(('name_city_country', f"{name}, {city}, {country}"))
    
    # Query 2: nombre + ciudad
    if name and city:
        queries.append(('name_city', f"{name}, {city}"))
    
    # Query 3: nombre + país
    if name and country:
        queries.append(('name_country', f"{name}, {country}"))
    
    # Query 4: solo nombre
    if name:
        queries.append(('name_only', name))
    
    return queries

def enrich_site_with_nominatim(site_data):
    """Enriquece un sitio con datos de Nominatim"""
    queries = create_search_queries(site_data)
    
    for search_type, query in queries:
        print(f"🔍 Buscando: '{query}' ({search_type})")
        
        result = search_nominatim(query)
        
        if result:
            # Extraer información básica
            importance_score = result.get('importance', 0)
            quality_level = get_quality_level(importance_score)
            
            # Extraer información de Wikipedia
            wikipedia_info = extract_wikipedia_info(result)
            
            # Crear estructura de datos
            nominatim_data = {
                'found': True,
                'quality_score': importance_score,
                'quality_level': quality_level,
                'search_used': search_type,
                'query_used': query,
                'data': {
                    'osm_id': result.get('osm_id'),
                    'place_id': result.get('place_id'),
                    'lat': result.get('lat'),
                    'lon': result.get('lon'),
                    'display_name': result.get('display_name'),
                    'type': result.get('type'),
                    'importance': importance_score,
                    'class': result.get('class'),
                    **wikipedia_info
                }
            }
            
            print(f"✅ Encontrado: {result.get('display_name', 'N/A')} (score: {importance_score:.2f}, nivel: {quality_level})")
            return nominatim_data
        
        # Rate limiting: esperar 1 segundo entre búsquedas
        time.sleep(1)
    
    # Si no se encontró nada
    print(f"❌ No encontrado: {site_data.get('name', 'N/A')}")
    return {
        'found': False,
        'quality_score': 0,
        'quality_level': 'not_found',
        'search_used': 'none',
        'query_used': '',
        'data': {}
    }

def process_sites_with_nominatim(input_path, output_path):
    """Procesa todos los sitios con Nominatim y guarda los resultados"""
    
    print("🚀 INICIANDO ENRIQUECIMIENTO CON NOMINATIM")
    print("=" * 60)
    print(f"📥 Entrada: {input_path}")
    print(f"📤 Salida: {output_path}")
    print()
    
    # Cargar datos
    sites = []
    total_entities = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entity = json.loads(line)
                total_entities += 1
                
                # Solo procesar sitios
                if entity.get('entity_type') == 'site':
                    sites.append(entity)
    
    print(f"📊 Estadísticas:")
    print(f"   • Total de entidades: {total_entities}")
    print(f"   • Sitios a procesar: {len(sites)}")
    print()
    
    # Procesar cada sitio
    enriched_entities = []
    processed_count = 0
    
    for i, site in enumerate(sites, 1):
        print(f"🔄 Procesando sitio {i}/{len(sites)}: {site.get('name', 'Sin nombre')}")
        
        # Enriquecer con Nominatim
        nominatim_data = enrich_site_with_nominatim(site)
        
        # Añadir datos de Nominatim al sitio
        site['nominatim_match'] = nominatim_data
        enriched_entities.append(site)
        
        processed_count += 1
        
        # Mostrar progreso cada 10 sitios
        if i % 10 == 0:
            print(f"📈 Progreso: {i}/{len(sites)} sitios procesados")
        print()
    
    # Cargar todas las entidades originales y actualizar solo los sitios
    all_entities = []
    site_index = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entity = json.loads(line)
                
                # Si es un sitio, usar la versión enriquecida
                if entity.get('entity_type') == 'site':
                    all_entities.append(enriched_entities[site_index])
                    site_index += 1
                else:
                    # Mantener entidades que no son sitios sin cambios
                    all_entities.append(entity)
    
    # Guardar resultados
    with open(output_path, 'w', encoding='utf-8') as f:
        for entity in all_entities:
            f.write(json.dumps(entity, ensure_ascii=False) + '\n')
    
    # Estadísticas finales
    print("🎉 PROCESAMIENTO COMPLETADO")
    print("=" * 60)
    
    # Contar resultados por calidad
    quality_stats = defaultdict(int)
    found_count = 0
    
    for site in enriched_entities:
        nominatim_data = site.get('nominatim_match', {})
        if nominatim_data.get('found', False):
            found_count += 1
            quality_level = nominatim_data.get('quality_level', 'unknown')
            quality_stats[quality_level] += 1
    
    print(f"📊 Resultados:")
    print(f"   • Sitios procesados: {len(sites)}")
    print(f"   • Sitios encontrados: {found_count}")
    print(f"   • Tasa de éxito: {(found_count/len(sites)*100):.1f}%")
    print()
    print(f"🏆 Calidad de matches:")
    for level, count in sorted(quality_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count/found_count*100) if found_count > 0 else 0
        print(f"   • {level.capitalize()}: {count} ({percentage:.1f}%)")
    
    print(f"\n💾 Archivo guardado en: {output_path}")
    
    return {
        'total_sites': len(sites),
        'found_sites': found_count,
        'success_rate': found_count/len(sites) if sites else 0,
        'quality_stats': dict(quality_stats)
    }

def show_sample_results(output_path, num_samples=5):
    """Muestra ejemplos de resultados enriquecidos"""
    print(f"\n📋 EJEMPLOS DE RESULTADOS (primeros {num_samples})")
    print("=" * 60)
    
    sites_shown = 0
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            if sites_shown >= num_samples:
                break
                
            entity = json.loads(line)
            if entity.get('entity_type') == 'site':
                nominatim_data = entity.get('nominatim_match', {})
                
                print(f"📍 {entity.get('name', 'Sin nombre')}")
                print(f"   • Ciudad: {entity.get('city', 'N/A')}")
                print(f"   • País: {entity.get('country', 'N/A')}")
                print(f"   • Encontrado: {nominatim_data.get('found', False)}")
                
                if nominatim_data.get('found'):
                    data = nominatim_data.get('data', {})
                    print(f"   • OSM ID: {data.get('osm_id', 'N/A')}")
                    print(f"   • Wikipedia: {data.get('wikipedia_id', 'N/A')}")
                    print(f"   • Coordenadas: {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}")
                    print(f"   • Calidad: {nominatim_data.get('quality_level', 'N/A')} ({nominatim_data.get('quality_score', 0):.2f})")
                    print(f"   • Búsqueda usada: {nominatim_data.get('search_used', 'N/A')}")
                else:
                    print(f"   • No encontrado en Nominatim")
                
                print()
                sites_shown += 1

if __name__ == "__main__":
    # Rutas de archivos
    input_file = r"D:\TravelApp\Project\scripts\data\scraper_enrichment\enriched_data_3.jsonl"
    output_file = r"D:\TravelApp\Project\scripts\data\scraper_enrichment\enriched_data_4.jsonl"
    
    # Procesar sitios
    stats = process_sites_with_nominatim(input_file, output_file)
    
    # Mostrar ejemplos
    show_sample_results(output_file) 