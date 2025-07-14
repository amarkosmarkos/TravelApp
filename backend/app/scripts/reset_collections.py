import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_collections():
    # Conectar a MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.travel_app

    try:
        # Lista de colecciones a limpiar
        collections = [
            "travels",
            "conversations",
            "messages",
            "itineraries",
            "itinerary_items",
            "visits",
            "places",
            "flights"
        ]

        # Limpiar cada colección
        for collection in collections:
            await db[collection].delete_many({})
            logger.info(f"Colección {collection} limpiada")

        # Crear índices necesarios
        await db.travels.create_index("user_id")
        await db.conversations.create_index("travel_id")
        await db.messages.create_index([("conversation_id", 1), ("travel_id", 1)])
        await db.messages.create_index("timestamp")
        
        # Crear índice único en travel_id para itinerarios
        itineraries = db["itineraries"]
        itineraries.create_index("travel_id", unique=True)
        
        logger.info("Índices creados correctamente")
        logger.info("Reset completado exitosamente")

    except Exception as e:
        logger.error(f"Error durante el reset: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(reset_collections()) 