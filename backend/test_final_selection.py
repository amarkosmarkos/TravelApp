#!/usr/bin/env python3
"""
Script para probar el flujo final con selección de destinos.
"""

import asyncio
import sys
import os
from pathlib import Path

# Configurar el path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow
from app.database import connect_to_mongodb, close_mongodb_connection

async def test_final_flow():
    """Prueba el flujo final completo."""
    try:
        print("🎯 Probando flujo final con selección de destinos...")
        
        # Conectar a MongoDB
        await connect_to_mongodb()
        print("✅ Conectado a MongoDB")
        
        # Crear instancia del workflow
        workflow = SmartItineraryWorkflow()
        
        # Probar diferentes mensajes
        test_cases = [
            {
                "message": "Quiero ir a Tailandia por 7 días",
                "expected_days": 7
            },
            {
                "message": "Tailandia por 3 días",
                "expected_days": 3
            },
            {
                "message": "Quiero visitar Tailandia",
                "expected_days": 7  # Default
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n{'='*60}")
            print(f"PRUEBA {i+1}: '{test_case['message']}'")
            print(f"{'='*60}")
            
            # Extraer días
            total_days = workflow._extract_days_from_message(test_case['message'])
            print(f"📅 Días extraídos: {total_days} (esperado: {test_case['expected_days']})")
            
            # Simular procesamiento
            response = await workflow.process_smart_request(
                user_input=test_case['message'],
                user_id="test_user_123",
                travel_id="test_travel_123",
                country="thailand"
            )
            
            print(f"✅ Respuesta generada:")
            print(f"   Intención: {response.get('intention', 'unknown')}")
            print(f"   Workflow state: {response.get('workflow_state', {})}")
            
            # Verificar que se seleccionaron ciudades
            workflow_state = response.get('workflow_state', {})
            selected_count = workflow_state.get('selected_cities_count', 0)
            total_count = workflow_state.get('total_available_count', 0)
            
            if selected_count > 0:
                print(f"✅ Selección exitosa: {selected_count} ciudades de {total_count} disponibles")
            else:
                print(f"❌ No se seleccionaron ciudades")
            
            # Mostrar parte del mensaje
            message = response.get('message', '')
            if len(message) > 200:
                message = message[:200] + "..."
            print(f"📝 Mensaje: {message}")
        
        print(f"\n✅ Todas las pruebas completadas")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongodb_connection()

if __name__ == "__main__":
    asyncio.run(test_final_flow()) 