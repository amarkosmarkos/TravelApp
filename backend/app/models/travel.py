from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from bson import ObjectId
from .base import PyObjectId, MongoBaseModel

class MessageBase(BaseModel):
    content: str
    is_user: bool = True
    travel_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class TravelBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    destination: str
    budget: Optional[float] = None
    status: str = "active"

class TravelCreate(TravelBase):
    pass

class TravelUpdate(TravelBase):
    title: Optional[str] = None
    destination: Optional[str] = None

class Travel(TravelBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Message] = []

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class ChatBase(BaseModel):
    travel_id: str
    title: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class ChatMessageBase(BaseModel):
    content: str
    is_user: bool = True

class ChatMessageCreate(ChatMessageBase):
    travel_id: str

class ChatMessage(ChatMessageBase, MongoBaseModel):
    travel_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ItineraryBase(BaseModel):
    pass

class ItineraryCreate(ItineraryBase):
    travel_id: str

class Itinerary(ItineraryBase, MongoBaseModel):
    travel_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ItineraryItemBase(BaseModel):
    day: int
    description: str

class ItineraryItemCreate(ItineraryItemBase):
    itinerary_id: str

class ItineraryItem(ItineraryItemBase, MongoBaseModel):
    itinerary_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VisitBase(BaseModel):
    pass

class VisitCreate(VisitBase):
    travel_id: str

class Visit(VisitBase, MongoBaseModel):
    travel_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlaceBase(BaseModel):
    pass

class PlaceCreate(PlaceBase):
    travel_id: str

class Place(PlaceBase, MongoBaseModel):
    travel_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FlightBase(BaseModel):
    pass

class FlightCreate(FlightBase):
    travel_id: str

class Flight(FlightBase, MongoBaseModel):
    travel_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 