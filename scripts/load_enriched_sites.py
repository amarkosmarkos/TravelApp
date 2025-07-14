import json
from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "travel_app"
COLLECTION = "sites"
JSONL_PATH = "D:\TravelApp\Project\scripts\data\scraper_enrichment\enriched_data_9.jsonl"

def load_enriched_sites():
    """Carga los sitios enriquecidos desde JSONL a MongoDB."""
    
    try:
        # Conectar a MongoDB
        print("Conectando a MongoDB...")
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        collection = db[COLLECTION]
        
        # Leer el archivo JSONL
        print(f"Leyendo archivo: {JSONL_PATH}")
        docs = []
        
        with open(JSONL_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    docs.append(doc)
        
        print(f"Se encontraron {len(docs)} sitios para cargar")
        
        # Limpiar la colección existente
        print("Limpiando colección existente...")
        collection.delete_many({})
        
        # Insertar los datos
        print("Insertando sitios en MongoDB...")
        if docs:
            result = collection.insert_many(docs)
            print(f"Se insertaron {len(result.inserted_ids)} sitios exitosamente")
        
        print("¡Carga completada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la carga: {str(e)}")
        raise
    finally:
        # Cerrar conexión
        client.close()

if __name__ == "__main__":
    load_enriched_sites() 