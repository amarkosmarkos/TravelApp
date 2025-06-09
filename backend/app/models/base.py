from typing import Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from bson import ObjectId
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if not ObjectId.is_valid(str(v)):
            raise ValueError("Invalid ObjectId")
        return ObjectId(str(v))

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator: GetJsonSchemaHandler, _schema: JsonSchemaValue) -> JsonSchemaValue:
        return {"type": "string", "description": "ObjectId"}

    def __str__(self):
        return str(self)

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    }

    @property
    def mongo_id(self) -> str:
        return str(self.id) if self.id else None 