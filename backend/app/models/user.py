from pydantic import BaseModel, EmailStr
from typing import Optional


# This is the input model used when receiving data from the user (for registration).
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str  # This is the password field that should be hashed on registration.

# This is the output model used when returning data from the database (includes the MongoDB-generated `id`).
class UserInDB(UserCreate):
    id: Optional[str]  # MongoDB automatically generates the `id`
    hashed_password: str  # The password is hashed before being stored

