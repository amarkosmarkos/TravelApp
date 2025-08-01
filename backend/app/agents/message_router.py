"""
Router central que decide qué hacer con cada mensaje del usuario.
"""

from typing import Dict, Any, List
from enum import Enum
import logging
from openai import AzureOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Tipos de mensajes que puede procesar el sistema."""
    CREATE_ITINERARY = "create_itinerary"
    MODIFY_ITINERARY = "modify_itinerary"
    SEARCH_CITIES = "search_cities"
    OPTIMIZE_ROUTE = "optimize_route"
    GENERAL_CHAT = "general_chat"
    ERROR = "error"

class MessageRouter:
    """
    Router central que clasifica y dirige mensajes a los agentes correctos.
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
        Clasifica el mensaje del usuario y determina qué acción tomar.
        """
        try:
            # Análisis rápido con keywords
            quick_analysis = self._quick_classification(message)
            
            # Si es claro, usar clasificación rápida
            if quick_analysis["confidence"] > 0.8:
                return quick_analysis
            
            # Si no es claro, usar AI para clasificar
            return await self._ai_classification(message, context)
            
        except Exception as e:
            logger.error(f"Error clasificando mensaje: {e}")
            return {
                "type": MessageType.GENERAL_CHAT,
                "confidence": 0.5,
                "reason": "Error en clasificación"
            }
    
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
            
            # Usar el flujo inteligente
            from .smart_itinerary_workflow import SmartItineraryWorkflow
            smart_workflow = SmartItineraryWorkflow()
            
            # Obtener historial de mensajes si está disponible
            travel_messages = context.get("message_history", []) if context else []
            
            # Procesar con el flujo inteligente
            response = await smart_workflow.process_smart_request(
                user_input=message,
                user_id=user_id,
                travel_id=travel_id,
                country=country  # Usar el país extraído
            )
            
            # Agregar información de clasificación (convertir enum a string)
            message_type = classification.get("type", MessageType.GENERAL_CHAT)
            response["classification"] = {
                "type": message_type.value if hasattr(message_type, 'value') else str(message_type),
                "confidence": classification.get("confidence", 0.0),
                "reason": classification.get("reason", "Clasificación AI: UNKNOWN"),
                "extracted_country": country
            }
            
            return response
            
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