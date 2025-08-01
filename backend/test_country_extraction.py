#!/usr/bin/env python3
"""
Test para verificar la extracción de países del mensaje.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.message_router import message_router

async def test_country_extraction():
    """Test de extracción de países."""
    try:
        print("🌍 Probando extracción de países...")
        
        # Test 1: Tailandia
        print("\n🇹🇭 Test 1: Tailandia")
        message_thailand = "Quiero un itinerario para Tailandia"
        country_thailand = await message_router._extract_country_from_message(message_thailand)
        print(f"   Mensaje: {message_thailand}")
        print(f"   País extraído: {country_thailand}")
        
        # Test 2: Japón
        print("\n🇯🇵 Test 2: Japón")
        message_japan = "Quiero crear un itinerario para Japón"
        country_japan = await message_router._extract_country_from_message(message_japan)
        print(f"   Mensaje: {message_japan}")
        print(f"   País extraído: {country_japan}")
        
        # Test 3: España
        print("\n🇪🇸 Test 3: España")
        message_spain = "Diseña un viaje a España"
        country_spain = await message_router._extract_country_from_message(message_spain)
        print(f"   Mensaje: {message_spain}")
        print(f"   País extraído: {country_spain}")
        
        # Test 4: Francia
        print("\n🇫🇷 Test 4: Francia")
        message_france = "Quiero ir a Francia"
        country_france = await message_router._extract_country_from_message(message_france)
        print(f"   Mensaje: {message_france}")
        print(f"   País extraído: {country_france}")
        
        # Test 5: Sin país específico
        print("\n❓ Test 5: Sin país específico")
        message_generic = "Quiero un viaje"
        country_generic = await message_router._extract_country_from_message(message_generic)
        print(f"   Mensaje: {message_generic}")
        print(f"   País extraído: {country_generic}")
        
        print("\n✅ Extracción de países probada!")
        
    except Exception as e:
        print(f"❌ Error en test de países: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_country_extraction()) 