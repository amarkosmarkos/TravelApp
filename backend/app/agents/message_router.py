"""
Central router that decides what to do with each user message.
"""

from typing import Dict, Any, List
from enum import Enum
import logging
from openai import AzureOpenAI
from app.config import settings
import aiohttp

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages that the system can process."""
    CREATE_ITINERARY = "create_itinerary"
    MODIFY_ITINERARY = "modify_itinerary"
    SEARCH_CITIES = "search_cities"
    OPTIMIZE_ROUTE = "optimize_route"
    GENERAL_CHAT = "general_chat"
    ERROR = "error"

class MessageRouter:
    """
    Central router that classifies and directs messages to the correct agents.
    """
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    
    async def classify_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classifies the user message and determines what action to take.
        """
        try:
            # 0) Try with Azure Language (CLU) if configured
            clu_result = await self._clu_classification(message, context)
            if clu_result and clu_result.get("confidence", 0) >= 0.8:
                return clu_result
            # Quick analysis with keywords
            quick_analysis = self._quick_classification(message)
            
            # If clear, use quick classification
            if quick_analysis["confidence"] > 0.8:
                return quick_analysis
            
            # If not clear, use AI with function calling (tools)
            tool_cls = await self._tool_classification(message, context)
            if tool_cls:
                return tool_cls
            # Fallback to simple AI classification
            return await self._ai_classification(message, context)
            
        except Exception as e:
            logger.error(f"Error classifying message: {e}")
            return {
                "type": MessageType.GENERAL_CHAT,
                "confidence": 0.5,
                "reason": "Classification error"
            }

    async def _clu_classification(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any] | None:
        """
        Usa Azure Language (Conversational Language Understanding) si hay credenciales.
        Devuelve dict con type y confidence o None si no aplica.
        """
        try:
            if not (settings.AZURE_LANGUAGE_ENDPOINT and settings.AZURE_LANGUAGE_KEY and settings.AZURE_LANGUAGE_PROJECT and settings.AZURE_LANGUAGE_DEPLOYMENT):
                return None
            url = f"{settings.AZURE_LANGUAGE_ENDPOINT.rstrip('/')}/language/:analyze-conversations?api-version=2023-04-01"
            payload = {
                "kind": "Conversation",
                "analysisInput": {
                    "conversationItem": {
                        "id": "1",
                        "participantId": "user",
                        "text": message
                    },
                    "isLoggingEnabled": False
                },
                "parameters": {
                    "projectName": settings.AZURE_LANGUAGE_PROJECT,
                    "deploymentName": settings.AZURE_LANGUAGE_DEPLOYMENT,
                    "verbose": False
                }
            }
            headers = {"Ocp-Apim-Subscription-Key": settings.AZURE_LANGUAGE_KEY, "Content-Type": "application/json"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()
            # Parse CLU top intent
            top = (data.get("result") or {}).get("prediction", {}).get("topIntent")
            score_map = (data.get("result") or {}).get("prediction", {}).get("intents", [])
            score = 0.0
            for it in score_map:
                if it.get("category") == top:
                    score = float(it.get("confidenceScore", 0))
                    break
            mapping = {
                "CREATE_ITINERARY": MessageType.CREATE_ITINERARY,
                "MODIFY_ITINERARY": MessageType.MODIFY_ITINERARY,
                "SEARCH_CITIES": MessageType.SEARCH_CITIES,
                "OPTIMIZE_ROUTE": MessageType.OPTIMIZE_ROUTE,
                "GENERAL_CHAT": MessageType.GENERAL_CHAT,
                "PREFERENCES": MessageType.GENERAL_CHAT
            }
            mtype = mapping.get(top, MessageType.GENERAL_CHAT)
            return {"type": mtype, "confidence": score, "reason": f"CLU:{top}"}
        except Exception as e:
            logger.warning(f"CLU classification failed: {e}")
            return None
    
    def _quick_classification(self, message: str) -> Dict[str, Any]:
        """
        Clasificación rápida basada en keywords.
        """
        message_lower = message.lower()
        
        # Patrones para crear itinerario
        create_patterns = [
            "crear itinerario", "hacer itinerario", "planificar viaje",
            "quiero ir a", "me gustaría visitar", "plan de viaje"
        ]
        
        # Patrones para modificar
        modify_patterns = [
            "añadir", "agregar", "add", "quitar", "eliminar", "remove",
            "borrar", "cambiar", "modificar", "actualizar", "update"
        ]
        
        # Patrones para optimizar
        optimize_patterns = [
            "optimizar", "mejorar", "optimize", "ruta", "orden",
            "más eficiente", "mejor ruta"
        ]
        
        # Patrones para buscar
        search_patterns = [
            "buscar", "encontrar", "qué hay en", "ciudades de",
            "sitios de", "lugares de"
        ]
        
        # Verificar patrones
        if any(pattern in message_lower for pattern in create_patterns):
            return {
                "type": MessageType.CREATE_ITINERARY,
                "confidence": 0.9,
                "reason": "Patrón de creación detectado"
            }
        
        if any(pattern in message_lower for pattern in modify_patterns):
            return {
                "type": MessageType.MODIFY_ITINERARY,
                "confidence": 0.85,
                "reason": "Patrón de modificación detectado"
            }
        
        if any(pattern in message_lower for pattern in optimize_patterns):
            return {
                "type": MessageType.OPTIMIZE_ROUTE,
                "confidence": 0.8,
                "reason": "Patrón de optimización detectado"
            }
        
        if any(pattern in message_lower for pattern in search_patterns):
            return {
                "type": MessageType.SEARCH_CITIES,
                "confidence": 0.75,
                "reason": "Patrón de búsqueda detectado"
            }
        
        # Si no coincide con nada, chat general
        return {
            "type": MessageType.GENERAL_CHAT,
            "confidence": 0.6,
            "reason": "No se detectaron patrones específicos"
        }
    
    async def _ai_classification(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Clasificación usando AI para casos complejos.
        """
        try:
            prompt = f"""
Analiza este mensaje del usuario y clasifícalo:

MENSAJE: "{message}"

CONTEXTO: {context or "Sin contexto adicional"}

OPCIONES:
1. CREATE_ITINERARY - Quiere crear un nuevo itinerario de viaje
2. MODIFY_ITINERARY - Quiere modificar un itinerario existente
3. SEARCH_CITIES - Quiere buscar ciudades o sitios
4. OPTIMIZE_ROUTE - Quiere optimizar una ruta existente
5. GENERAL_CHAT - Conversación general o pregunta

Responde SOLO con el tipo en mayúsculas (ej: CREATE_ITINERARY)
"""

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un clasificador de mensajes. Responde SOLO con el tipo."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            classification = response.choices[0].message.content.strip()
            
            # Mapear respuesta a enum
            type_mapping = {
                "CREATE_ITINERARY": MessageType.CREATE_ITINERARY,
                "MODIFY_ITINERARY": MessageType.MODIFY_ITINERARY,
                "SEARCH_CITIES": MessageType.SEARCH_CITIES,
                "OPTIMIZE_ROUTE": MessageType.OPTIMIZE_ROUTE,
                "GENERAL_CHAT": MessageType.GENERAL_CHAT
            }
            
            return {
                "type": type_mapping.get(classification, MessageType.GENERAL_CHAT),
                "confidence": 0.7,
                "reason": f"Clasificación AI: {classification}"
            }
            
        except Exception as e:
            logger.error(f"Error en clasificación AI: {e}")
            return {
                "type": MessageType.GENERAL_CHAT,
                "confidence": 0.5,
                "reason": "Error en clasificación AI"
            }

    async def _tool_classification(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any] | None:
        """
        Clasificación usando function calling para obtener intent y slots estructurados.
        Devuelve dict con type, confidence, reason, extracted_country, total_days, preferences si tiene éxito.
        """
        try:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "route_intent",
                        "description": "Clasifica la intención del usuario y extrae slots relevantes",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intent": {
                                    "type": "string",
                                    "enum": [
                                        "CREATE_ITINERARY", "MODIFY_ITINERARY",
                                        "PREFERENCES", "SEARCH_CITIES",
                                        "OPTIMIZE_ROUTE", "GENERAL_CHAT"
                                    ]
                                },
                                "country": {"type": "string"},
                                "total_days": {"type": "integer"},
                                "preferences": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["intent"]
                        }
                    }
                }
            ]

            sys = "Eres un router de mensajes. Invoca la función con la intención y slots."
            ctx_txt = f"CONTEXTO: {context or {}}"
            resp = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"MENSAJE: {message}\n{ctx_txt}"}
                ],
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=300
            )

            choice = resp.choices[0]
            msg = choice.message
            import json
            # Modo tools (OpenAI/Azure moderno)
            tool_calls = getattr(msg, "tool_calls", None)
            args = None
            if tool_calls and len(tool_calls) > 0:
                call = tool_calls[0]
                fn_name = getattr(call.function, "name", None)
                if fn_name == "route_intent":
                    args = json.loads(getattr(call.function, "arguments", "{}") or "{}")
            # Fallback a function_call (APIs antiguos)
            if args is None:
                fn_call = getattr(msg, "function_call", None)
                if fn_call and getattr(fn_call, "name", None) == "route_intent":
                    args = json.loads(getattr(fn_call, "arguments", "{}") or "{}")
            if args is None:
                return None
            intent = args.get("intent", "GENERAL_CHAT")
            country = args.get("country")
            total_days = args.get("total_days")
            preferences = args.get("preferences") or []

            type_mapping = {
                "CREATE_ITINERARY": MessageType.CREATE_ITINERARY,
                "MODIFY_ITINERARY": MessageType.MODIFY_ITINERARY,
                "SEARCH_CITIES": MessageType.SEARCH_CITIES,
                "OPTIMIZE_ROUTE": MessageType.OPTIMIZE_ROUTE,
                "PREFERENCES": MessageType.GENERAL_CHAT,  # se eleva a CREATE en capa superior si hay config
                "GENERAL_CHAT": MessageType.GENERAL_CHAT
            }
            return {
                "type": type_mapping.get(intent, MessageType.GENERAL_CHAT),
                "confidence": 0.85,
                "reason": f"tool_call:{intent}",
                "extracted_country": country,
                "total_days": total_days,
                "preferences": preferences
            }
        except Exception as e:
            logger.warning(f"Tool classification failed: {e}")
            return None
    
    async def _extract_country_from_message(self, message: str) -> str:
        """
        Extrae el país del mensaje del usuario.
        """
        try:
            # Mapeo de países
            country_mapping = {
                "thailand": "thailand", "tailandia": "thailand", "tailandés": "thailand",
                "japan": "japan", "japón": "japan", "japon": "japan", "japones": "japan",
                "spain": "spain", "españa": "spain", "espania": "spain", "español": "spain",
                "france": "france", "francia": "france", "francés": "france",
                "italy": "italy", "italia": "italy", "italiano": "italy",
                "germany": "germany", "alemania": "germany", "alemán": "germany",
                "uk": "uk", "united kingdom": "uk", "reino unido": "uk", "inglaterra": "uk",
                "usa": "usa", "united states": "usa", "estados unidos": "usa", "america": "usa"
            }
            
            # Convertir a minúsculas para búsqueda
            message_lower = message.lower()
            
            # Buscar países en el mensaje
            for country_key, country_code in country_mapping.items():
                if country_key in message_lower:
                    return country_code
            
            # Si no se encuentra, devolver thailand por defecto
            return "thailand"
            
        except Exception as e:
            logger.error(f"Error extrayendo país del mensaje: {e}")
            return "thailand"
    
    async def route_message(self, message: str, user_id: str, travel_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Clasifica y enruta el mensaje del usuario.
        """
        try:
            # Clasificar el mensaje
            classification = await self.classify_message(message, context)
            
            # Extraer el país del mensaje
            country = await self._extract_country_from_message(message)
            logger.info(f"País extraído del mensaje: {country}")
            
            # Decidir acción según intención (gating)
            message_type = classification.get("type", MessageType.GENERAL_CHAT)
            confidence = classification.get("confidence", 0.0)
            type_str = message_type.value if hasattr(message_type, 'value') else str(message_type)

            # Umbral de confianza para acciones automáticas
            auto_threshold = 0.75

            # Solo crear/modificar si la intención es clara
            if type_str in (MessageType.CREATE_ITINERARY.value, MessageType.MODIFY_ITINERARY.value) or (
                message_type in (MessageType.CREATE_ITINERARY, MessageType.MODIFY_ITINERARY)
            ):
                from .smart_itinerary_workflow import SmartItineraryWorkflow
                smart_workflow = SmartItineraryWorkflow()

                response = await smart_workflow.process_smart_request(
                    user_input=message,
                    user_id=user_id,
                    travel_id=travel_id,
                    country=country
                )

                response["classification"] = {
                    "type": type_str if isinstance(type_str, str) else (message_type.value if hasattr(message_type, 'value') else str(message_type)),
                    "confidence": confidence,
                    "reason": classification.get("reason", "Clasificación AI: UNKNOWN"),
                    "extracted_country": country
                }
                return response

            # Para búsquedas/optimización: responder sin alterar itinerarios
            if type_str == MessageType.SEARCH_CITIES.value or message_type == MessageType.SEARCH_CITIES:
                return {
                    "message": "¿Qué país o ciudad quieres explorar? Puedo mostrarte opciones y luego crear el itinerario si te encaja.",
                    "is_user": False,
                    "intention": "search_cities",
                    "classification": {
                        "type": MessageType.SEARCH_CITIES.value,
                        "confidence": confidence,
                        "reason": classification.get("reason", "Clasificación AI: SEARCH_CITIES"),
                        "extracted_country": country
                    }
                }

            if type_str == MessageType.OPTIMIZE_ROUTE.value or message_type == MessageType.OPTIMIZE_ROUTE:
                return {
                    "message": "Puedo optimizar tu ruta actual. ¿Quieres mantener las mismas ciudades y ordenar por menor desplazamiento, o prefieres cambiar también ciudades?",
                    "is_user": False,
                    "intention": "optimize_route_query",
                    "classification": {
                        "type": MessageType.OPTIMIZE_ROUTE.value,
                        "confidence": confidence,
                        "reason": classification.get("reason", "Clasificación AI: OPTIMIZE_ROUTE"),
                        "extracted_country": country
                    }
                }

            # Si es chat general o confianza baja: pedir aclaración en vez de crear nada
            if (type_str == MessageType.GENERAL_CHAT.value or message_type == MessageType.GENERAL_CHAT) or confidence < auto_threshold:
                return {
                    "message": "¡Hola! ¿Quieres que te cree un itinerario o modificar uno existente? Dime país y duración aproximada (por ejemplo, 14 días) y el estilo (playa, historia, naturaleza, gastronomía).",
                    "is_user": False,
                    "intention": "clarify",
                    "classification": {
                        "type": MessageType.GENERAL_CHAT.value,
                        "confidence": confidence,
                        "reason": classification.get("reason", "Baja confianza o chat general"),
                        "extracted_country": country
                    }
                }

            # Fallback por si llega un tipo desconocido
            return {
                "message": "¿Quieres crear un nuevo itinerario o prefieres que revisemos el actual?",
                "is_user": False,
                "intention": "clarify",
                "classification": {
                    "type": str(type_str),
                    "confidence": confidence,
                    "reason": classification.get("reason", "Tipo no reconocido"),
                    "extracted_country": country
                }
            }
            
        except Exception as e:
            logger.error(f"Error en routing con LangChain: {e}")
            # Fallback al sistema original si hay error
            try:
                response = {
                    "message": "Lo siento, hubo un error procesando tu mensaje. Usando sistema de respaldo.",
                    "is_user": False,
                    "intention": "error"
                }
                response["classification"] = {
                    "type": "error",
                    "confidence": 0.0,
                    "reason": f"Error en routing: {str(e)}",
                    "extracted_country": "thailand"
                }
                return response
            except Exception as fallback_error:
                logger.error(f"Error en fallback: {fallback_error}")
                return {
                    "message": "Lo siento, hubo un error crítico procesando tu mensaje.",
                    "is_user": False,
                    "intention": "error",
                    "classification": {
                        "type": "critical_error",
                        "confidence": 0.0,
                        "reason": f"Error crítico: {str(fallback_error)}",
                        "extracted_country": "thailand"
                    }
                }

# Instancia global
message_router = MessageRouter() 