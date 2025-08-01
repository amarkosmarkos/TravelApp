#!/usr/bin/env python3
"""
Script para verificar la estructura de los sites en la base de datos.
"""

import asyncio
import sys
import os
from pathlib import Path

# Configurar el path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from app.database import get_sites_collection, connect_to_mongodb, close_mongodb_connection

async def check_sites_structure():
    """Verifica la estructura de los sites en la BD."""
    try:
        # Conectar a la base de datos
        await connect_to_mongodb()
        
        # Obtener colección de sites
        sites_collection = await get_sites_collection()
        
        # Buscar algunos sites de ejemplo
        sites = await sites_collection.find({}).limit(5).to_list(length=None)
        
        print(f"📊 Encontrados {len(sites)} sites de ejemplo")
        
        for i, site in enumerate(sites):
            print(f"\n🏛️ Site {i+1}:")
            print(f"   ID: {site.get('_id')}")
            print(f"   Nombre: {site.get('name')}")
            print(f"   Tipo: {site.get('type')}")
            print(f"   Entity Type: {site.get('entity_type')}")
            print(f"   Subtype: {site.get('subtype')}")
            print(f"   Lat (original): {site.get('lat')} (tipo: {type(site.get('lat'))})")
            print(f"   Lon (original): {site.get('lon')} (tipo: {type(site.get('lon'))})")
            
            # Probar conversión
            try:
                lat_float = float(site.get("lat", "0")) if site.get("lat") else None
                lon_float = float(site.get("lon", "0")) if site.get("lon") else None
                print(f"   Lat (convertido): {lat_float}")
                print(f"   Lon (convertido): {lon_float}")
                print(f"   ✅ Conversión exitosa")
            except (ValueError, TypeError) as e:
                print(f"   ❌ Error en conversión: {e}")
            
            print(f"   Wikidata ID: {site.get('wikidata_id')}")
            print(f"   Hierarchy: {site.get('hierarchy')}")
        
        print(f"\n✅ Verificación de estructura completada")
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
    finally:
        await close_mongodb_connection()

if __name__ == "__main__":
    asyncio.run(check_sites_structure()) 