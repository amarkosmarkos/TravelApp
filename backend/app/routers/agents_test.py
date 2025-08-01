"""
Endpoint de prueba para el sistema de agentes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.agent_service import agent_service

router = APIRouter(prefix="/agents", tags=["agents"])

logger = logging.getLogger(__name__)

@router.post("/test")
async def test_agents(message: str) -> Dict[str, Any]:
    """
    Prueba el sistema de agentes con un mensaje.
    """
    try:
        logger.info(f"Probando agentes con mensaje: {message}")
        
        # Procesar con agentes
        response = await agent_service.process_message_with_agents(
            message=message,
            user_id="test_user",
            use_workflow=True
        )
        
        return {
            "success": True,
            "message": response["message"],
            "intention": response.get("intention", "unknown"),
            "agent_system": response.get("agent_system", "unknown"),
            "workflow_used": response.get("workflow_used", False)
        }
        
    except Exception as e:
        logger.error(f"Error en test de agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_agent_status() -> Dict[str, Any]:
    """
    Obtiene el estado de los agentes.
    """
    try:
        status = agent_service.get_agent_status()
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_agent_connection() -> Dict[str, Any]:
    """
    Prueba la conexión de los agentes.
    """
    try:
        result = await agent_service.test_agent_connection()
        return {
            "success": True,
            "connection_test": result
        }
        
    except Exception as e:
        logger.error(f"Error en test de conexión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-cities")
async def search_cities(country: str) -> Dict[str, Any]:
    """
    Busca ciudades usando el agente de base de datos.
    """
    try:
        result = await agent_service.search_cities_with_agents(country)
        return {
            "success": True,
            "search_result": result
        }
        
    except Exception as e:
        logger.error(f"Error buscando ciudades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-itinerary")
async def create_itinerary(country: str, cities: list = None, preferences: dict = None) -> Dict[str, Any]:
    """
    Crea un itinerario usando el sistema de agentes.
    """
    try:
        result = await agent_service.create_itinerary_with_agents(
            country=country,
            cities=cities,
            preferences=preferences
        )
        return {
            "success": True,
            "itinerary_result": result
        }
        
    except Exception as e:
        logger.error(f"Error creando itinerario: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 