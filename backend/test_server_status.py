#!/usr/bin/env python3
"""
Script para verificar el estado del servidor.
"""

import requests
import json
import sys
import os
from pathlib import Path

# Configurar el path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

def test_server_status():
    """Verifica el estado del servidor."""
    try:
        # Test 1: Verificar que el servidor esté corriendo
        print("🔍 Verificando estado del servidor...")
        
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está corriendo correctamente")
            print(f"   Respuesta: {response.json()}")
        else:
            print(f"❌ Servidor respondió con código: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor en http://localhost:8000")
        print("   Asegúrate de que el servidor esté ejecutándose con: python start_server.py")
        return False
    except Exception as e:
        print(f"❌ Error verificando servidor: {e}")
        return False
    
    # Test 2: Verificar endpoint de sitios disponibles
    try:
        print("\n🔍 Verificando endpoint de sitios...")
        
        response = requests.get("http://localhost:8000/api/travels/sites/available?country_code=TH", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint de sitios funciona")
            print(f"   Sitios encontrados: {data.get('total_count', 0)}")
        else:
            print(f"❌ Endpoint de sitios falló: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando endpoint de sitios: {e}")
    
    # Test 3: Verificar endpoint de itinerarios
    try:
        print("\n🔍 Verificando endpoint de itinerarios...")
        
        # Usar un travel_id de prueba
        test_travel_id = "test_travel_123"
        response = requests.get(f"http://localhost:8000/api/travels/{test_travel_id}/itinerary", timeout=5)
        
        if response.status_code in [200, 404]:
            print(f"✅ Endpoint de itinerarios responde (código: {response.status_code})")
            if response.status_code == 200:
                data = response.json()
                print(f"   Itinerarios encontrados: {len(data)}")
        else:
            print(f"❌ Endpoint de itinerarios falló: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verificando endpoint de itinerarios: {e}")
    
    print("\n✅ Verificación de servidor completada")
    return True

if __name__ == "__main__":
    test_server_status() 