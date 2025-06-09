from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from .base import PyObjectId, MongoBaseModel

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

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

class UserInDB(UserBase, MongoBaseModel):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    @classmethod
    def from_mongo(cls, data: dict):
        """Convertir documento de MongoDB a UserInDB"""
        if not data:
            return None
        id = data.pop('_id', None)
        return cls(**dict(data, _id=id))

class User(UserBase, MongoBaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

# Roles y permisos predefinidos
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
    return ROLES.get(role, [])

