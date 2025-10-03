"""
Chat service that orchestrates the conversation with the travel assistant.
All user-facing messages can be localized via utils.i18n.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from app.database import get_messages_collection, get_itineraries_collection
from app.models.travel import ChatMessageCreate, Message
from bson import ObjectId
from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow
from app.agents.message_router import MessageRouter, MessageType
from app.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for chat message processing and itinerary workflows.
    """
    
    def __init__(self):
        self.smart_workflow = SmartItineraryWorkflow()
        self.message_router = MessageRouter()
        # Anti-duplicados simple en memoria: (user, travel, msg_norm) -> timestamp
        self._recent_messages: Dict[str, float] = {}
        self._recent_ttl_sec = 3.0
    
    async def process_message(self, message: str, user_id: str, travel_id: str, db=None, preferred_language: str | None = None) -> Dict[str, Any]:
        """
        Process a user message using SmartItineraryWorkflow.
        """
        try:
            # Demo short-circuit
            if settings.MOCK_MODE:
                demo_reply = (
                    "[DEMO] ¡Hola! Esta es una respuesta simulada. "
                    "Puedo enseñarte un itinerario de ejemplo por Tailandia (Bangkok, Chiang Mai, Phuket) "
                    "y darte sugerencias de hoteles y transporte. Escribe tus preferencias."
                )
                return {
                    "message": demo_reply,
                    "is_user": False,
                    "intention": "demo_reply",
                    "classification": {
                        "type": "demo",
                        "confidence": 1.0,
                        "reason": "MOCK_MODE enabled",
                        "extracted_country": "thailand"
                    },
                    "travel_id": travel_id,
                    "user_id": user_id
                }

            logger.info(f"Processing message: {message}")
            from app.utils.language import detect_preferred_language
            from app.utils.i18n import t
            lang = preferred_language or detect_preferred_language(message)

            # Dedup: avoid processing same message within a short window
            import time
            msg_norm = (message or "").strip().lower()
            dedup_key = f"{user_id}:{travel_id}:{msg_norm}"
            now = time.time()
            last_ts = self._recent_messages.get(dedup_key)
            if last_ts and (now - last_ts) < self._recent_ttl_sec:
                logger.info("Duplicate message detected; ignoring")
                # Return neutral message so WS won't broadcast
                return {
                    "message": "",
                    "is_user": False,
                    "intention": "duplicate_ignored",
                    "classification": {
                        "type": "duplicate",
                        "confidence": 1.0,
                        "reason": t(lang, "duplicate_ignored"),
                        "extracted_country": ""
                    },
                    "travel_id": travel_id,
                    "user_id": user_id
                }
            # Registrar mensaje
            self._recent_messages[dedup_key] = now
            
            # Save user message
            await self._save_user_message(message, user_id, travel_id)

            # Early check: if travel does not exist, request new setup
            try:
                from app.database import get_travels_collection
                from bson import ObjectId
                travels = await get_travels_collection()
                tr_exists = await travels.find_one({"_id": ObjectId(travel_id)})
                if not tr_exists:
                    assistant_message = t(lang, "travel_not_found")
                    await self._save_assistant_message(assistant_message, user_id, travel_id)
                    return {
                        "message": assistant_message,
                        "is_user": False,
                        "intention": "clarify",
                        "classification": {
                            "type": "clarify",
                            "confidence": 1.0,
                            "reason": "travel_not_found",
                            "extracted_country": ""
                        },
                        "travel_id": travel_id,
                        "user_id": user_id
                    }
            except Exception as e:
                logger.warning(f"Could not verify travel existence {travel_id}: {e}")

            # Build travel context for intent classification
            travel_ctx = {}
            try:
                from app.database import get_travels_collection, get_itineraries_collection
                travels = await get_travels_collection()
                itineraries = await get_itineraries_collection()
                tr = await travels.find_one({"_id": ObjectId(travel_id)})
                it = await itineraries.find_one({"travel_id": travel_id})
                if tr:
                    travel_ctx = {
                        "travel_id": travel_id,
                        "country": tr.get("country") or tr.get("destination"),
                        "total_days": tr.get("total_days"),
                        "has_setup": bool((tr.get("country") or tr.get("destination")) and tr.get("total_days")),
                        "has_itinerary": bool(it is not None)
                    }
            except Exception as e:
                logger.warning(f"Could not build travel context: {e}")

            # Classify intent (gating) with function calling
            classification = await self.message_router.classify_message(message, context=travel_ctx)
            message_type = classification.get("type", MessageType.GENERAL_CHAT)
            confidence = classification.get("confidence", 0.0)
            # Prefer country/total_days from classification/tools o contexto
            country = classification.get("extracted_country") or travel_ctx.get("country") or self._extract_country_from_message(message) or "thailand"
            extracted_days = classification.get("total_days")

            # Threshold for auto-actions
            auto_threshold = 0.75

            # If general chat or low confidence, clarify instead of creating
            # EXCEPT when TravelSetup is present and message looks like preferences → trigger create itinerary
            if (message_type == MessageType.GENERAL_CHAT) or (confidence < auto_threshold and message_type not in (MessageType.CREATE_ITINERARY, MessageType.MODIFY_ITINERARY)):
                try:
                    # Check travel setup
                    from app.database import get_travels_collection
                    travels = await get_travels_collection()
                    tr = await travels.find_one({"_id": ObjectId(travel_id)})
                    if tr and (tr.get("destination") or tr.get("country")) and (tr.get("total_days")):
                        # Treat as preferences and create itinerary
                        logger.info("Preferences detected with TravelSetup. Triggering itinerary creation.")
                        country_eff = (tr.get("country") or tr.get("destination") or country)
                        total_days = int(extracted_days or tr.get("total_days") or 7)
                        response = await self.smart_workflow.process_smart_request(
                            user_input=message,
                            user_id=user_id,
                            travel_id=travel_id,
                            country=country_eff
                        )
                        assistant_message = response.get("message", "Itinerary created.")
                        await self._save_assistant_message(assistant_message, user_id, travel_id)
                        logger.info(f"Itinerary triggered by preferences. country={country_eff}, total_days={total_days}")
                        return {
                            "message": assistant_message,
                            "is_user": False,
                            "intention": response.get("intention", "itinerary_created"),
                            "classification": classification,
                            "travel_id": travel_id,
                            "user_id": user_id
                        }
                except Exception as e:
                    logger.warning(f"Failed to trigger by preferences with TravelSetup: {e}")
                assistant_message = t(lang, "clarify_prompt")
                await self._save_assistant_message(assistant_message, user_id, travel_id)
                return {
                    "message": assistant_message,
                    "is_user": False,
                    "intention": "clarify",
                    "classification": {
                        "type": message_type.value if hasattr(message_type, 'value') else str(message_type),
                        "confidence": confidence,
                        "reason": classification.get("reason", "low_confidence_or_general_chat"),
                        "extracted_country": country
                    },
                    "travel_id": travel_id,
                    "user_id": user_id
                }
            
            # Use the smart workflow (destination selection before the graph)
            response = await self.smart_workflow.process_smart_request(
                user_input=message,
                user_id=user_id,
                travel_id=travel_id,
                country=country
            )
            
            # Ensure message is present
            assistant_message = response.get("message", "Sorry, I couldn't process your message.")
            
            # Save assistant response
            await self._save_assistant_message(assistant_message, user_id, travel_id)
            
            # Normalize classification to be JSON-serializable
            type_str = message_type.value if hasattr(message_type, 'value') else str(message_type)
            classification_out = {
                "type": type_str,
                "confidence": confidence,
                "reason": classification.get("reason", ""),
                "extracted_country": country
            }

            # Devolver respuesta con estructura correcta
            return {
                "message": assistant_message,
                "is_user": False,
                "intention": response.get("intention", "unknown"),
                "classification": response.get("classification", classification_out),
                "travel_id": travel_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            from app.utils.i18n import t
            error_message = t("en", "error_processing", error=str(e))
            await self._save_assistant_message(error_message, user_id, travel_id)
            return {
                "message": error_message,
                "is_user": False,
                "intention": "error"
            }
    
    async def _save_user_message(self, message: str, user_id: str, travel_id: str):
        """Guarda un mensaje del usuario en la base de datos."""
        try:
            messages_collection = await get_messages_collection()
            message_data = ChatMessageCreate(
                content=message,
                is_user=True,
                user_id=user_id,
                travel_id=travel_id
            )
            await messages_collection.insert_one(message_data.dict())
            logger.info(f"Mensaje del usuario guardado para travel {travel_id}")
        except Exception as e:
            logger.error(f"Error guardando mensaje del usuario: {e}")
    
    async def _save_assistant_message(self, message: str, user_id: str, travel_id: str):
        """Guarda un mensaje del asistente en la base de datos."""
        try:
            messages_collection = await get_messages_collection()
            message_data = ChatMessageCreate(
                content=message,
                is_user=False,
                user_id=user_id,
                travel_id=travel_id
            )
            await messages_collection.insert_one(message_data.dict())
            logger.info(f"Mensaje del asistente guardado para travel {travel_id}")
        except Exception as e:
            logger.error(f"Error guardando mensaje del asistente: {e}")
    
    async def get_chat_messages(self, travel_id: str, user_id: str, db, skip: int = 0, limit: int = 50) -> List[Dict]:
        try:
            # Demo short-circuit
            if settings.MOCK_MODE:
                now_iso = datetime.utcnow().isoformat()
                return [
                    {
                        "id": "mock-1",
                        "content": "Hola, soy tu asistente de viajes (demo). ¿A qué país te gustaría viajar?",
                        "is_user": False,
                        "timestamp": now_iso,
                        "user_id": "assistant",
                        "travel_id": travel_id
                    },
                    {
                        "id": "mock-2",
                        "content": "Muéstrame un itinerario por Tailandia de 7 días",
                        "is_user": True,
                        "timestamp": now_iso,
                        "user_id": user_id or "user",
                        "travel_id": travel_id
                    }
                ]

            logger.info(f"Getting chat messages for travel {travel_id}, user {user_id}")
            messages_collection = await get_messages_collection()
            messages = await messages_collection.find(
                {"travel_id": travel_id}
            ).sort("timestamp", 1).skip(skip).limit(limit).to_list(length=None)
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": str(msg["_id"]),
                    "content": msg["content"],
                    "is_user": msg["is_user"],
                    "timestamp": msg.get("timestamp", msg.get("created_at", datetime.utcnow())).isoformat(),
                    "user_id": msg.get("user_id", "unknown"),
                    "travel_id": msg["travel_id"]
                })
            logger.info(f"Retrieved {len(formatted_messages)} messages for travel {travel_id}")
            return formatted_messages
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []
    
    async def create_message(self, message_data: ChatMessageCreate) -> Dict[str, Any]:
        """Crea un nuevo mensaje en la base de datos."""
        try:
            if settings.MOCK_MODE:
                return {"id": "mock-created", "success": True}
            messages_collection = await get_messages_collection()
            result = await messages_collection.insert_one(message_data.dict())
            return {"id": str(result.inserted_id), "success": True}
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return {"success": False, "error": str(e)}

    def _extract_country_from_message(self, message: str) -> str:
        """
        Extracts the country from the user's message.
        """
        message_lower = message.lower()
        
        # Country mapping
        country_mapping = {
            "tailandia": "thailand",
            "thailand": "thailand",
            "thai": "thailand",
            "tailandesa": "thailand",
            "bangkok": "thailand",
            "chiang mai": "thailand",
            "phuket": "thailand",
            "krabi": "thailand",
            "ayutthaya": "thailand",
            "pataya": "thailand",
            "pattaya": "thailand",
            "koh samui": "thailand",
            "koh phangan": "thailand",
            "koh tao": "thailand"
        }
        
        for keyword, country_code in country_mapping.items():
            if keyword in message_lower:
                return country_code
        
        return "thailand"  # Default

# Instancia global
chat_service = ChatService() 