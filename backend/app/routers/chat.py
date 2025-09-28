from fastapi import APIRouter, Depends, HTTPException, Request
from app.services.chat_service import chat_service
from app.utils.authentication import verify_jwt_token
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/api", tags=["chat"])

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    history: Optional[List[ChatMessage]] = Field(default=None, description="Chat history")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant's response")
    history: List[ChatMessage] = Field(..., description="Updated chat history")

class TravelSetupRequest(BaseModel):
    """Configuración inicial del viaje."""
    start_date: datetime = Field(..., description="Fecha de inicio del viaje")
    total_days: int = Field(..., description="Número total de días")
    country: str = Field(..., description="País de destino")
    origin_city: Optional[str] = Field(default="", description="Ciudad de origen")
    companions: Optional[str] = Field(default="solo", description="Tipo de viaje (solo, pareja, familia, amigos)")
    preferences: Optional[dict] = Field(default={}, description="Preferencias adicionales")

class TravelSetupResponse(BaseModel):
    """Respuesta del setup de viaje."""
    success: bool = Field(..., description="Si el setup fue exitoso")
    message: str = Field(..., description="Mensaje de confirmación")
    travel_id: Optional[str] = Field(default=None, description="ID del viaje creado")

# Diccionario para almacenar el historial de chat por usuario
chat_histories = {}

# Diccionario para almacenar configuración de viajes por usuario
travel_setups = {}

async def get_current_user(token: str = Depends(verify_jwt_token)):
    email = verify_jwt_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email

@router.post("/travel/setup", response_model=TravelSetupResponse)
async def setup_travel(request: TravelSetupRequest, token: str = Depends(verify_jwt_token)):
    """
    Configuración inicial del viaje antes de comenzar el chat.
    """
    try:
        user_email = verify_jwt_token(token)
        
        # Generar ID único para el viaje
        import uuid
        travel_id = str(uuid.uuid4())
        
        # Guardar configuración del viaje
        travel_setups[user_email] = {
            "travel_id": travel_id,
            "start_date": request.start_date,
            "total_days": request.total_days,
            "country": request.country,
            "origin_city": request.origin_city,
            "companions": request.companions,
            "preferences": request.preferences,
            "created_at": datetime.utcnow()
        }
        
        return TravelSetupResponse(
            success=True,
            message=f"Configuración de viaje guardada: {request.total_days} días a {request.country} desde {request.start_date.strftime('%d/%m/%Y')}",
            travel_id=travel_id
        )
        
    except Exception as e:
        print(f"Error en setup de viaje: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error configurando el viaje: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, token: str = Depends(verify_jwt_token)):
    try:
        # Obtener el cuerpo de la solicitud como JSON
        body = await request.json()
        print("Cuerpo de la solicitud recibido:", json.dumps(body, indent=2))

        # Validar y convertir el cuerpo a ChatRequest
        chat_request = ChatRequest(**body)
        print(f"Mensaje validado: {chat_request.message}")
        print(f"Historial validado: {chat_request.history}")
        
        # Obtener usuario (email) y travel_id si vino en el payload
        user_email = verify_jwt_token(token)
        travel_id = (travel_setups.get(user_email, {}) or {}).get("travel_id")
        # Si hay travel_id almacenado pero el documento fue borrado en Mongo, regenerar uno efímero
        try:
            from bson import ObjectId
            from app.database import get_travels_collection
            if travel_id:
                travels = await get_travels_collection()
                tr = await travels.find_one({"_id": ObjectId(travel_id)})
                if not tr:
                    travel_id = None
        except Exception:
            pass
        if not travel_id:
            # Si no hay setup válido, generamos un travel_id efímero por compatibilidad
            import uuid
            travel_id = str(uuid.uuid4())

        # Pasar por ChatService (con gating) para respuesta consistente
        svc_response = await chat_service.process_message(
            message=chat_request.message,
            user_id=user_email,
            travel_id=travel_id
        )

        # Reconstruir historial de respuesta: anexar user y assistant
        updated_history = chat_request.history or []
        updated_history = updated_history + [
            ChatMessage(role="user", content=chat_request.message),
            ChatMessage(role="assistant", content=svc_response.get("message", ""))
        ]

        return ChatResponse(
            response=svc_response.get("message", ""),
            history=updated_history
        )
        
    except Exception as e:
        print(f"Error en el endpoint de chat: {str(e)}")
        if isinstance(e, ValueError):
            print(f"Detalles del error de validación: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el mensaje: {str(e)}"
        ) 