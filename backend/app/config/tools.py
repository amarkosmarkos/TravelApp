"""
Definition of available tools for the travel assistant.
"""

from typing import List, Dict, Any

def load_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of available tools for the assistant.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "create_itinerary",
                "description": """Creates or modifies a travel itinerary. This function MUST be used in the following cases:
                1. When the user mentions a country (with or without cities)
                2. When the user confirms they want to create an itinerary (says "yes", "ok", etc.)
                3. When the user asks to add or modify cities in an existing itinerary
                4. When the user mentions specific cities for a country
                
                IMPORTANT: 
                - If only country_name is provided, the function will automatically determine the country_code
                - If no cities are provided, the function will suggest the most relevant cities for that country
                - City names must be in English (e.g., 'Tokyo' instead of 'Tokio')
                - The country_code must be the correct ISO code (e.g., 'TH' for Thailand)
                - This function can handle both country names and country codes
                - Take initiative and suggest cities if none are provided""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of cities for the itinerary. Names MUST be in English (e.g., 'Tokyo', 'London', 'Paris'). Optional - if not provided, will suggest cities for the country."
                        },
                        "country_code": {
                            "type": "string",
                            "description": "ISO country code (e.g., TH for Thailand, JP for Japan, ES for Spain). Optional if country_name is provided."
                        },
                        "country_name": {
                            "type": "string",
                            "description": "Country name (e.g., 'Thailand', 'Japan', 'Spain'). Optional if country_code is provided."
                        }
                    },
                    "required": []
                }
            }
        }
    ] 