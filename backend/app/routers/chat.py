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
    """Initial travel configuration."""
    start_date: datetime = Field(..., description="Travel start date")
    total_days: int = Field(..., description="Total number of days")
    country: str = Field(..., description="Destination country")
    origin_city: Optional[str] = Field(default="", description="Origin city")
    companions: Optional[str] = Field(default="solo", description="Travel type (solo, couple, family, friends)")
    preferences: Optional[dict] = Field(default={}, description="Additional preferences")

class TravelSetupResponse(BaseModel):
    """Travel setup response."""
    success: bool = Field(..., description="Whether the setup was successful")
    message: str = Field(..., description="Confirmation message")
    travel_id: Optional[str] = Field(default=None, description="Created travel ID")

# Dictionary to store chat history per user
chat_histories = {}

# Dictionary to store travel configuration per user
travel_setups = {}

async def get_current_user(token: str = Depends(verify_jwt_token)):
    email = verify_jwt_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email

@router.post("/travel/setup", response_model=TravelSetupResponse)
async def setup_travel(request: TravelSetupRequest, token: str = Depends(verify_jwt_token)):
    """
    Initial travel configuration before starting the chat.
    """
    try:
        user_email = verify_jwt_token(token)
        
        # Generate unique ID for the travel
        import uuid
        travel_id = str(uuid.uuid4())
        
        # Save travel configuration
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
            message=f"Travel configuration saved: {request.total_days} days to {request.country} from {request.start_date.strftime('%d/%m/%Y')}",
            travel_id=travel_id
        )
        
    except Exception as e:
        print(f"Error in travel setup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring travel: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, token: str = Depends(verify_jwt_token)):
    try:
        # Get request body as JSON
        body = await request.json()
        print("Request body received:", json.dumps(body, indent=2))

        # Validate and convert body to ChatRequest
        chat_request = ChatRequest(**body)
        print(f"Validated message: {chat_request.message}")
        print(f"Validated history: {chat_request.history}")
        
        # Get user (email) and travel_id if it came in the payload
        user_email = verify_jwt_token(token)
        travel_id = (travel_setups.get(user_email, {}) or {}).get("travel_id")
        # If there's a stored travel_id but the document was deleted in Mongo, regenerate an ephemeral one
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
            # If there's no valid setup, generate an ephemeral travel_id for compatibility
            import uuid
            travel_id = str(uuid.uuid4())

        # Pass through ChatService (with gating) for consistent response
        svc_response = await chat_service.process_message(
            message=chat_request.message,
            user_id=user_email,
            travel_id=travel_id
        )

        # Reconstruct response history: append user and assistant
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
        print(f"Error in chat endpoint: {str(e)}")
        if isinstance(e, ValueError):
            print(f"Validation error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        ) 