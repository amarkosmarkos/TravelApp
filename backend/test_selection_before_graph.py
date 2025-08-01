#!/usr/bin/env python3
"""
Script para probar que la selección de destinos se hace ANTES del grafo.
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
from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow

async def test_selection_before_graph():
    """Prueba que la selección se hace ANTES del grafo."""
    try:
        # Conectar a la base de datos
        await connect_to_mongodb()
        
        # Obtener TODOS los sitios disponibles
        sites_collection = await get_sites_collection()
        all_sites = await sites_collection.find({
            "entity_type": "site",
            "subtype": "city"
        }).limit(20).to_list(length=None)
        
        print(f"📊 Total de sitios disponibles: {len(all_sites)}")
        
        # Mostrar algunos sitios
        for i, site in enumerate(all_sites[:5]):
            print(f"   {i+1}. {site.get('name')} - {site.get('type')}")
        
        # Probar diferentes mensajes del usuario
        test_messages = [
            "Quiero ir a Tailandia por 7 días",
            "Tailandia por 3 días",
            "Quiero visitar Tailandia",  # Sin especificar días
            "Fin de semana en Tailandia",
            "Viaje largo a Tailandia"
        ]
        
        for message in test_messages:
            print(f"\n🎯 Probando: '{message}'")
            print("=" * 60)
            
            # Extraer días del mensaje
            workflow = SmartItineraryWorkflow()
            total_days = workflow._extract_days_from_message(message)
            print(f"📅 Días extraídos: {total_days}")
            
            # IA selecciona destinos ANTES del grafo
            selection = await destination_selection_agent.select_destinations(
                country="thailand",
                total_days=total_days,
                available_sites=all_sites,
                user_preferences=None
            )
            
            if selection.get("error"):
                print(f"❌ Error: {selection['error']}")
                continue
            
            selected_cities = selection.get("selected_cities", [])
            print(f"✅ IA seleccionó {len(selected_cities)} destinos de {len(all_sites)} disponibles")
            
            # Mostrar ciudades seleccionadas
            for i, city in enumerate(selected_cities):
                print(f"   {i+1}. {city['name']} - {city['days']} días")
                print(f"      Razón: {city.get('reason', 'No especificada')}")
            
            # Mostrar información de tiempo
            exploration_days = selection.get("total_exploration_days", 0)
            transport_days = selection.get("estimated_transport_days", 0)
            total_travel_days = selection.get("total_travel_days", 0)
            
            print(f"\n⏰ Información de tiempo:")
            print(f"   Días de exploración: {exploration_days}")
            print(f"   Días de transporte: {transport_days}")
            print(f"   Total días de viaje: {total_travel_days}")
            
            # Verificar que no exceda los días disponibles
            available_days = total_days - 1  # 1 día para llegada/salida
            if total_travel_days > available_days:
                print(f"⚠️  ADVERTENCIA: Excede días disponibles ({total_travel_days} > {available_days})")
            else:
                print(f"✅ Días dentro del límite ({total_travel_days} <= {available_days})")
        
        print(f"\n✅ Prueba completada")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    finally:
        await close_mongodb_connection()

if __name__ == "__main__":
    asyncio.run(test_selection_before_graph()) 