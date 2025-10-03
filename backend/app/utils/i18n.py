"""
Simple i18n utility for user-facing messages.
All code-level strings and prompts are English; responses to users are localized via this module.
"""

from typing import Dict

_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "travel_not_found": "I can't find this trip configuration (it may have been deleted). Tell me the country and duration (e.g., 14 days) to create a new one, or run the initial setup again.",
        "clarify_prompt": "Hi! Would you like me to create or modify an itinerary? Tell me country and duration (e.g., 14 days) and the style (beach, history, nature, gastronomy).",
        "error_processing": "Sorry, there was an error processing your message: {error}",
        "duplicate_ignored": "Duplicate message ignored in a short window.",
    },
    "es": {
        "travel_not_found": "No encuentro la configuración de este viaje (posiblemente fue borrado). Indícame el país y la duración (por ejemplo, 14 días) para crear uno nuevo, o vuelve a realizar la configuración inicial.",
        "clarify_prompt": "¡Hola! ¿Quieres que te cree un itinerario o modificar uno existente? Dime país y duración (por ejemplo, 14 días) y el estilo (playa, historia, naturaleza, gastronomía).",
        "error_processing": "Lo siento, hubo un error procesando tu mensaje: {error}",
        "duplicate_ignored": "Mensaje duplicado detectado, ignorando procesamiento.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang_code = (lang or "en").split("-")[0].lower()
    table = _STRINGS.get(lang_code) or _STRINGS["en"]
    template = table.get(key) or _STRINGS["en"].get(key, key)
    try:
        return template.format(**kwargs)
    except Exception:
        return template


