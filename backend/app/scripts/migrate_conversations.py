import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_conversations():
    # Conectar a MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.travel_app

    try:
        # Obtener todos los viajes
        travels = await db.travels.find().to_list(length=None)
        logger.info(f"Encontrados {len(travels)} viajes para migrar")

        for travel in travels:
            travel_id = str(travel["_id"])
            user_id = travel["user_id"]

            # Verificar si ya existe una conversación para este viaje
            existing_conversation = await db.conversations.find_one({"travel_id": travel_id})
            
            if not existing_conversation:
                # Crear nueva conversación
                conversation = {
                    "travel_id": travel_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                result = await db.conversations.insert_one(conversation)
                conversation_id = str(result.inserted_id)
                logger.info(f"Creada conversación {conversation_id} para viaje {travel_id}")

                # Actualizar mensajes existentes con el conversation_id
                messages = await db.messages.find({"travel_id": travel_id}).to_list(length=None)
                if messages:
                    for message in messages:
                        await db.messages.update_one(
                            {"_id": message["_id"]},
                            {"$set": {"conversation_id": conversation_id}}
                        )
                    logger.info(f"Actualizados {len(messages)} mensajes para viaje {travel_id}")
            else:
                logger.info(f"Ya existe conversación para viaje {travel_id}")

        logger.info("Migración completada exitosamente")

    except Exception as e:
        logger.error(f"Error durante la migración: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_conversations()) 