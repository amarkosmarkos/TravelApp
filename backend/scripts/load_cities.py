import sys
import os
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Añadir el directorio raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "travel_app"

async def load_cities():
    try:
        # Conectar a MongoDB
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        cities_collection = db["cities"]
        
        # Leer el archivo CSV
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts', 'data', 'cities.csv')
        df = pd.read_csv(csv_path)
        
        # Convertir DataFrame a lista de diccionarios
        cities_data = df.to_dict('records')
        
        # Insertar los datos en la colección cities
        if cities_data:
            await cities_collection.insert_many(cities_data)
            print("Cities loaded successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(load_cities()) 