#!/usr/bin/env python3
"""
Script para probar la selección de destinos basada en tiempo.
"""

import asyncio
import sys
import os
from pathlib import Path

# Configurar el path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from app.database import get_sites_collection, connect_to_mongodb, close_mongodb_connection
from app.agents.destination_selection_agent import destination_selection_agent
from app.services.travel_time_service import travel_time_service

async def test_time_based_selection():
    """Prueba la selección de destinos basada en tiempo."""
    try:
        # Conectar a la base de datos
        await connect_to_mongodb()
        
        # Obtener sitios de Tailandia
        sites_collection = await get_sites_collection()
        sites = await sites_collection.find({
            "entity_type": "site",
            "subtype": "city"
        }).limit(10).to_list(length=None)
        
        print(f"📊 Encontrados {len(sites)} sitios para probar")
        
        # Probar diferentes duraciones de viaje
        test_cases = [
            {"days": 3, "description": "Viaje corto (3 días)"},
            {"days": 7, "description": "Viaje de una semana (7 días)"},
            {"days": 14, "description": "Viaje largo (14 días)"}
        ]
        
        for test_case in test_cases:
            print(f"\n🎯 {test_case['description']}")
            print("=" * 50)
            
            # IA selecciona destinos
            selection = await destination_selection_agent.select_destinations(
                country="thailand",
                total_days=test_case["days"],
                available_sites=sites,
                user_preferences=None
            )
            
            if selection.get("error"):
                print(f"❌ Error: {selection['error']}")
                continue
            
            selected_cities = selection.get("selected_cities", [])
            print(f"✅ IA seleccionó {len(selected_cities)} destinos:")
            
            for i, city in enumerate(selected_cities):
                print(f"   {i+1}. {city['name']} - {city['days']} días")
                print(f"      Razón: {city.get('reason', 'No especificada')}")
                print(f"      Coordenadas: {city['coordinates']}")
            
            # Mostrar información de tiempo
            exploration_days = selection.get("total_exploration_days", 0)
            transport_days = selection.get("estimated_transport_days", 0)
            total_travel_days = selection.get("total_travel_days", 0)
            
            print(f"\n⏰ Información de tiempo:")
            print(f"   Días de exploración: {exploration_days}")
            print(f"   Días de transporte: {transport_days}")
            print(f"   Total días de viaje: {total_travel_days}")
            
            # Mostrar segmentos de transporte
            travel_segments = selection.get("travel_segments", [])
            if travel_segments:
                print(f"\n🚌 Segmentos de transporte:")
                for segment in travel_segments:
                    travel_info = segment["travel_info"]
                    print(f"   {segment['from']} → {segment['to']}")
                    print(f"      Método: {travel_info['method']}")
                    print(f"      Duración: {travel_info['duration']}h")
                    print(f"      Tiempo aeropuerto: {travel_info['airport_time']}h")
                    print(f"      Total: {travel_info['total_time']}h")
                    print(f"      Distancia: {travel_info['distance']}km")
        
        print(f"\n✅ Prueba completada")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    finally:
        await close_mongodb_connection()

async def test_travel_time_calculation():
    """Prueba el cálculo de tiempo de viaje."""
    try:
        print("\n🔍 Probando cálculo de tiempo de viaje...")
        
        # Ciudades de ejemplo con coordenadas
        test_cities = [
            {
                "name": "Bangkok",
                "coordinates": {"latitude": 13.7563, "longitude": 100.5018}
            },
            {
                "name": "Chiang Mai",
                "coordinates": {"latitude": 18.7883, "longitude": 98.9853}
            },
            {
                "name": "Phuket",
                "coordinates": {"latitude": 7.8804, "longitude": 98.3923}
            }
        ]
        
        print(f"📊 Calculando tiempo entre {len(test_cities)} ciudades...")
        
        # Calcular tiempo total
        travel_info = travel_time_service.calculate_total_travel_time(test_cities)
        
        print(f"⏰ Tiempo total: {travel_info['total_time']} horas")
        print(f"📅 Días de transporte: {travel_info['total_days']}")
        
        # Mostrar segmentos
        for segment in travel_info["segments"]:
            travel_info_segment = segment["travel_info"]
            print(f"   {segment['from']} → {segment['to']}: {travel_info_segment['total_time']}h")
        
        print(f"✅ Cálculo de tiempo completado")
        
    except Exception as e:
        print(f"❌ Error en cálculo de tiempo: {e}")

if __name__ == "__main__":
    asyncio.run(test_time_based_selection())
    asyncio.run(test_travel_time_calculation()) 