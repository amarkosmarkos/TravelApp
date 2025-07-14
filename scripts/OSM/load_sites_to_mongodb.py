import json
import asyncio
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar los módulos
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.database import connect_to_mongodb, close_mongodb_connection, get_sites_collection
from app.config import settings

# Configuración de rutas
ENRICHED_FILE = Path(__file__).parent.parent / "scripts" / "data" / "scraper_enrichment" / "enriched_data_9.jsonl"

async def load_enriched_sites_to_mongodb():
    """Carga los sitios enriquecidos desde el JSONL a MongoDB en la colección 'sites'."""
    
    if not ENRICHED_FILE.exists():
        print(f"Error: El archivo {ENRICHED_FILE} no existe.")
        return
    
    try:
        # Conectar a MongoDB
        print("Conectando a MongoDB...")
        await connect_to_mongodb()
        
        # Obtener la colección de sitios
        sites_collection = await get_sites_collection()
        
        # Leer el archivo JSONL
        print(f"Leyendo archivo: {ENRICHED_FILE}")
        sites_data = []
        
        with open(ENRICHED_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    site = json.loads(line)
                    sites_data.append(site)
        
        print(f"Se encontraron {len(sites_data)} sitios para cargar")
        
        # Limpiar la colección existente (opcional)
        print("Limpiando colección existente...")
        await sites_collection.delete_many({})
        
        # Insertar los datos
        print("Insertando sitios en MongoDB...")
        if sites_data:
            result = await sites_collection.insert_many(sites_data)
            print(f"Se insertaron {len(result.inserted_ids)} sitios exitosamente")
        
        print("¡Carga completada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la carga: {str(e)}")
        raise
    finally:
        # Cerrar conexión
        await close_mongodb_connection()

def main():
    """Función principal."""
    print("Iniciando carga de sitios enriquecidos a MongoDB...")
    asyncio.run(load_enriched_sites_to_mongodb())

if __name__ == "__main__":
    main() 