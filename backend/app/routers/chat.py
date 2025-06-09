from fastapi import APIRouter, Depends, HTTPException, Request
from app.chat_model import chat_model
from app.utils.authentication import verify_jwt_token
from pydantic import BaseModel, Field
from typing import List, Optional
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

# Diccionario para almacenar el historial de chat por usuario
chat_histories = {}

async def get_current_user(token: str = Depends(verify_jwt_token)):
    email = verify_jwt_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email

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
        
        # Convertir el historial al formato esperado por el modelo
        chat_history = None
        if chat_request.history:
            chat_history = [{"role": msg.role, "content": msg.content} for msg in chat_request.history]
        
        # Generar respuesta
        response, updated_history = chat_model.generate_response(chat_request.message, chat_history)
        
        # Convertir el historial actualizado al formato de respuesta
        formatted_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in updated_history
        ]
        
        print(f"Respuesta generada: {response}")
        print(f"Historial actualizado: {formatted_history}")
        
        return ChatResponse(
            response=response,
            history=formatted_history
        )
        
    except Exception as e:
        print(f"Error en el endpoint de chat: {str(e)}")
        if isinstance(e, ValueError):
            print(f"Detalles del error de validación: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el mensaje: {str(e)}"
        ) 