from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from .base import PyObjectId, MongoBaseModel

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str  # ID del usuario
    exp: Optional[datetime] = None

# Base user model
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    permissions: List[str] = []
    roles: List[str] = []

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }

# User creation model
class UserCreate(UserBase):
    password: str

# User update model
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

# Database user model
class UserInDB(UserBase, MongoBaseModel):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    @classmethod
    def from_mongo(cls, data: dict):
        """Convert MongoDB document to UserInDB"""
        if not data:
            return None
        id = data.pop('_id', None)
        return cls(**dict(data, _id=id))

# Response user model
class User(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_superuser: bool = False

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            PyObjectId: str
        }
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False
            }
        }

# Predefined roles and permissions
ROLES = {
    "admin": [
        "manage_users",
        "manage_roles",
        "manage_travels",
        "view_reports"
    ],
    "manager": [
        "manage_travels",
        "view_reports"
    ],
    "user": [
        "create_travel",
        "view_own_travels",
        "edit_own_travels"
    ]
}

def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a given role"""
    return ROLES.get(role, [])

