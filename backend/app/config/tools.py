"""
Definición de las herramientas disponibles para el asistente de viajes.
"""

from typing import List, Dict, Any

def load_tools() -> List[Dict[str, Any]]:
    """
    Retorna la lista de herramientas disponibles para el asistente.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "create_itinerary",
                "description": """Crea o modifica un itinerario de viaje. Esta función DEBE ser usada en los siguientes casos:
                1. Cuando el usuario solicita crear un nuevo itinerario
                2. Cuando el usuario pide añadir o modificar ciudades en un itinerario existente
                3. Cuando el usuario menciona un país o región para planificar un viaje
                
                IMPORTANTE: 
                - Los nombres de las ciudades deben estar en inglés (ej: 'Tokyo' en lugar de 'Tokio')
                - Si el usuario solo menciona un país, DEBES sugerir las ciudades más relevantes para un viaje en ese país
                - NO preguntes al usuario por las ciudades, usa tu conocimiento para sugerir las más apropiadas""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de ciudades para el itinerario. Los nombres DEBEN estar en inglés (ej: 'Tokyo', 'London', 'Paris')."
                        },
                        "country_code": {
                            "type": "string",
                            "description": "Código de país ISO (ej: JP para Japón, ES para España, FR para Francia)"
                        }
                    },
                    "required": ["cities", "country_code"]
                }
            }
        }
    ] 