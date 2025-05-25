from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Coordinates(BaseModel):
    latitude: float = Field(..., description="Latitude of the city")
    longitude: float = Field(..., description="Longitude of the city")

class City(BaseModel):
    id: Optional[str] = Field(None, description="MongoDB document ID")
    name: str = Field(..., description="Name of the city")
    country: str = Field(..., description="ISO country code")
    population: int = Field(..., description="City population")
    latitude: float = Field(..., description="City latitude")
    longitude: float = Field(..., description="City longitude")
    timezone: Optional[str] = Field(None, description="City timezone")
    region: Optional[str] = Field(None, description="Region code")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Bangkok",
                "country": "TH",
                "population": 5104476,
                "latitude": 13.75398,
                "longitude": 100.50144,
                "timezone": "Asia/Bangkok",
                "region": "40"
            }
        } 