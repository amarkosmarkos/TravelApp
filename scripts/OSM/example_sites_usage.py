import asyncio
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar los módulos
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.database import connect_to_mongodb, close_mongodb_connection, get_sites_collection

async def example_sites_queries():
    """Ejemplos de consultas a la colección de sitios turísticos."""
    
    try:
        # Conectar a MongoDB
        print("Conectando a MongoDB...")
        await connect_to_mongodb()
        
        # Obtener la colección de sitios
        sites_collection = await get_sites_collection()
        
        # Ejemplo 1: Contar total de sitios
        total_sites = await sites_collection.count_documents({})
        print(f"\n1. Total de sitios turísticos: {total_sites}")
        
        # Ejemplo 2: Buscar sitios por tipo de turismo
        tourism_sites = await sites_collection.count_documents({
            "tags.tourism": {"$exists": True}
        })
        print(f"2. Sitios con tag 'tourism': {tourism_sites}")
        
        # Ejemplo 3: Buscar hoteles
        hotels = await sites_collection.find({
            "tags.tourism": "hotel"
        }).limit(5).to_list(length=5)
        
        print(f"\n3. Primeros 5 hoteles encontrados:")
        for hotel in hotels:
            print(f"   - {hotel.get('name', 'Sin nombre')} (ID: {hotel['osm_id']})")
        
        # Ejemplo 4: Buscar restaurantes
        restaurants = await sites_collection.find({
            "tags.amenity": "restaurant"
        }).limit(5).to_list(length=5)
        
        print(f"\n4. Primeros 5 restaurantes encontrados:")
        for restaurant in restaurants:
            print(f"   - {restaurant.get('name', 'Sin nombre')} (ID: {restaurant['osm_id']})")
        
        # Ejemplo 5: Buscar sitios históricos
        historic_sites = await sites_collection.find({
            "tags.historic": {"$exists": True}
        }).limit(5).to_list(length=5)
        
        print(f"\n5. Primeros 5 sitios históricos encontrados:")
        for site in historic_sites:
            print(f"   - {site.get('name', 'Sin nombre')} (Tipo: {site['tags'].get('historic', 'N/A')})")
        
        # Ejemplo 6: Buscar por ubicación geográfica (ejemplo: cerca de coordenadas específicas)
        # Nota: Para búsquedas geográficas más complejas, necesitarías índices geoespaciales
        print(f"\n6. Sitios con coordenadas:")
        sites_with_location = await sites_collection.find({
            "location": {"$exists": True}
        }).limit(3).to_list(length=3)
        
        for site in sites_with_location:
            location = site.get('location', {})
            print(f"   - {site.get('name', 'Sin nombre')}: {location.get('lat', 'N/A')}, {location.get('lon', 'N/A')}")
        
        # Ejemplo 7: Estadísticas por tipo de OSM
        pipeline = [
            {"$group": {"_id": "$osm_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        osm_type_stats = await sites_collection.aggregate(pipeline).to_list(length=None)
        print(f"\n7. Estadísticas por tipo de OSM:")
        for stat in osm_type_stats:
            print(f"   - {stat['_id']}: {stat['count']} sitios")
        
    except Exception as e:
        print(f"Error durante las consultas: {str(e)}")
        raise
    finally:
        # Cerrar conexión
        await close_mongodb_connection()

def main():
    """Función principal."""
    print("Ejemplos de consultas a sitios turísticos en MongoDB...")
    asyncio.run(example_sites_queries())

if __name__ == "__main__":
    main() 