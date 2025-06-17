import pandas as pd
import os
from pathlib import Path
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.config.settings import settings

async def load_cities_to_mongodb():
    # Conectar a MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    cities_collection = db.cities
    
    try:
        # Read the CSV file using absolute path
        csv_path = Path(__file__).parent / "data" / "cities.csv"
        if not csv_path.exists():
            print(f"Cities CSV file not found at {csv_path}. Please run download_cities.py first.")
            return
        
        df = pd.read_csv(csv_path)
        
        # Preparar los documentos para MongoDB
        cities = []
        for _, row in df.iterrows():
            city = {
                "name": row['name'],
                "country": row['country'],
                "country_code": row['country_code'] if 'country_code' in row else None,
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "timezone": row['timezone'],
                "population": int(row['population']) if pd.notna(row['population']) else None,
                "region": row['region'],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            cities.append(city)
        
        # Insertar en MongoDB
        if cities:
            await cities_collection.insert_many(cities)
            print(f"Loaded {len(cities)} cities into MongoDB")
            
            # Verificar la carga
            count = await cities_collection.count_documents({})
            print(f"Total cities in database: {count}")
        
    except Exception as e:
        print(f"Error loading data into MongoDB: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(load_cities_to_mongodb()) 