from ..utils.database import users_collection
from app.schemas.user import User, UserInDB
from passlib.context import CryptContext
from fastapi import HTTPException
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

# Crea un contexto para cifrado
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_user(user: UserInDB):
    try:
        user_dict = user.dict()
        print(f"Attempting to create user with data: {user_dict}")
        
        # Asegurarse de que no hay campos None
        user_dict = {k: v for k, v in user_dict.items() if v is not None}
        
        result = await users_collection.insert_one(user_dict)
        print(f"User created with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except DuplicateKeyError:
        print("Duplicate key error - email already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

async def get_user_by_email(email: str):
    try:
        print(f"Searching for user with email: {email}")
        user = await users_collection.find_one({"email": email})
        
        if user:
            print(f"User found: {user}")
            # Convertir ObjectId a string para la serialización
            user["id"] = str(user["_id"])
            return user
            
        print(f"No user found with email: {email}")
        return None
    except Exception as e:
        print(f"Error searching for user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching user: {str(e)}")

