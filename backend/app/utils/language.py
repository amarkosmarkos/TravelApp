"""
Language utilities to detect user preferred language.
Primary source: Azure Language (if configured via MessageRouter).
Fallback: simple heuristic; default to English.
"""

import re
from typing import Optional


_SPANISH_HINTS = re.compile(r"[ñÑáéíóúÁÉÍÓÚ¡¿]|\b(el|la|los|las|un|una|de|y|para|con|hola)\b", re.IGNORECASE)


def detect_preferred_language(message: str, router_language: Optional[str] = None, default: str = "en") -> str:
    if router_language:
        return router_language
    text = (message or "").strip()
    if not text:
        return default
    if _SPANISH_HINTS.search(text):
        return "es"
    return default


