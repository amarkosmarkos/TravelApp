from fastapi import APIRouter, Depends, HTTPException, Request
from app.travel_assistant import travel_assistant
from app.utils.authentication import verify_jwt_token
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["travel"])

class TravelRequest(BaseModel):
    message: str = Field(..., description="User's message")

class TravelResponse(BaseModel):
    intention: str = Field(..., description="Detected intention (reformulate_itinerary, other, error)")
    cities: List[dict] = Field(..., description="List of cities with their details")
    user_message: str = Field(..., description="Response message for the user")

@router.post("/travel", response_model=TravelResponse)
async def process_travel_request(request: Request, token: str = Depends(verify_jwt_token)):
    try:
        body = await request.json()
        travel_request = TravelRequest(**body)
        
        response = await travel_assistant.process_message(travel_request.message)
        return TravelResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing travel request: {str(e)}"
        ) 