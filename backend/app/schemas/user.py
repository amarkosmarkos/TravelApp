from pydantic import BaseModel, EmailStr
from typing import Optional

# Input schema for user registration
class User(BaseModel):
    email: EmailStr
    name: str
    password: str  # Plain password to be hashed

# Output schema for users stored in the database
class UserInDB(BaseModel):
    email: EmailStr
    name: str
    hashed_password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
