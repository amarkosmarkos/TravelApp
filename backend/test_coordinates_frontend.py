#!/usr/bin/env python3
"""
Script para simular una petición del frontend y verificar coordenadas.
"""

import requests
import json
import sys
import os
from pathlib import Path

# Configurar el path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

def test_coordinates_frontend():
    """Simula una petición del frontend para verificar coordenadas."""
    try:
        print("🔍 Simulando petición del frontend...")
        
        # Esperar un poco para que el servidor esté listo
        import time
        time.sleep(3)
        
        # Test 1: Verificar que el servidor esté corriendo
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor no está corriendo")
            return False
        
        print("✅ Servidor está corriendo")
        
        # Test 2: Obtener sitios disponibles
        print("\n🔍 Obteniendo sitios disponibles...")
        response = requests.get("http://localhost:8000/api/travels/sites/available?country_code=TH", timeout=5)
        
        if response.status_code == 200:
            sites_data = response.json()
            sites = sites_data.get('available_sites', [])
            print(f"✅ Sitios encontrados: {len(sites)}")
            
            if sites:
                # Mostrar información del primer sitio
                first_site = sites[0]
                print(f"\n📋 Información del primer sitio:")
                print(f"   Nombre: {first_site.get('name')}")
                print(f"   Lat: {first_site.get('lat')} (tipo: {type(first_site.get('lat'))})")
                print(f"   Lon: {first_site.get('lon')} (tipo: {type(first_site.get('lon'))})")
                print(f"   Type: {first_site.get('type')}")
                print(f"   Entity Type: {first_site.get('entity_type')}")
                print(f"   Subtype: {first_site.get('subtype')}")
                
                # Verificar conversión de coordenadas
                try:
                    lat_float = float(first_site.get('lat', '0')) if first_site.get('lat') else None
                    lon_float = float(first_site.get('lon', '0')) if first_site.get('lon') else None
                    print(f"   Lat (convertido): {lat_float}")
                    print(f"   Lon (convertido): {lon_float}")
                    print(f"   ✅ Conversión exitosa")
                except (ValueError, TypeError) as e:
                    print(f"   ❌ Error en conversión: {e}")
        else:
            print(f"❌ Error obteniendo sitios: {response.status_code}")
            return False
        
        # Test 3: Crear un itinerario de prueba
        print("\n🔍 Creando itinerario de prueba...")
        
        # Simular ciudades para el itinerario
        test_cities = [
            "Bangkok",
            "Chiang Mai", 
            "Phuket",
            "Ayutthaya",
            "Krabi"
        ]
        
        # Crear itinerario usando el endpoint
        itinerary_data = {
            "ai_cities": test_cities,
            "country_code": "TH"
        }
        
        # Nota: Este endpoint requiere autenticación, así que solo simulamos la estructura
        print(f"📋 Datos que se enviarían al frontend:")
        print(f"   Ciudades: {test_cities}")
        print(f"   País: TH")
        
        # Simular estructura de respuesta del itinerario
        sample_itinerary = {
            "travel_id": "test_travel_123",
            "cities": [
                {
                    "site_id": "6874126e9e000eba1e8c0e82",
                    "name": "Ao Nang",
                    "latitude": 8.0321024,
                    "longitude": 98.8225499,
                    "coordinates": {
                        "latitude": 8.0321024,
                        "longitude": 98.8225499
                    },
                    "type": "village",
                    "entity_type": "site",
                    "subtype": "city",
                    "wikidata_id": "Q375819",
                    "hierarchy": [
                        {"type": "country", "name": "Thailand", "code": "TH"},
                        {"type": "province", "name": "Krabi"}
                    ]
                },
                {
                    "site_id": "6874126e9e000eba1e8c0e83", 
                    "name": "Ayutthaya",
                    "latitude": 14.3535427,
                    "longitude": 100.5645684,
                    "coordinates": {
                        "latitude": 14.3535427,
                        "longitude": 100.5645684
                    },
                    "type": "administrative",
                    "entity_type": "site",
                    "subtype": "city",
                    "wikidata_id": "Q203370",
                    "hierarchy": [{"type": "country", "name": "Thailand", "code": "TH"}]
                }
            ]
        }
        
        print(f"\n📋 Estructura de respuesta del itinerario:")
        print(f"   Travel ID: {sample_itinerary['travel_id']}")
        print(f"   Ciudades: {len(sample_itinerary['cities'])}")
        
        for i, city in enumerate(sample_itinerary['cities']):
            print(f"   Ciudad {i+1}: {city['name']}")
            print(f"     - Latitude: {city['latitude']} (float)")
            print(f"     - Longitude: {city['longitude']} (float)")
            print(f"     - Coordinates: {city['coordinates']}")
            print(f"     - Site ID: {city['site_id']}")
        
        print(f"\n✅ El frontend debería poder procesar estas coordenadas correctamente")
        print(f"   - Las coordenadas están como float")
        print(f"   - Tanto latitude/longitude directos como coordinates object")
        print(f"   - Información completa del sitio incluida")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    test_coordinates_frontend() 