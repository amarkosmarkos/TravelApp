from ..utils.database import get_users_collection
from app.models.user import User, UserInDB, UserCreate, UserUpdate
from passlib.context import CryptContext
from fastapi import HTTPException
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from typing import List, Optional
from app.core.security import verify_password, get_password_hash

# Create encryption context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_user(user: UserInDB):
    try:
        user_dict = user.dict()
        print(f"Attempting to create user with data: {user_dict}")
        
        # Ensure there are no None fields
        user_dict = {k: v for k, v in user_dict.items() if v is not None}
        
        result = await get_users_collection().insert_one(user_dict)
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
        user = await get_users_collection().find_one({"email": email})
        
        if user:
            print(f"User found: {user}")
            # Convert ObjectId to string for serialization
            user["id"] = str(user["_id"])
            return user
            
        print(f"No user found with email: {email}")
        return None
    except Exception as e:
        print(f"Error searching for user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching user: {str(e)}")

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email"""
    users = await get_users_collection()
    user_data = await users.find_one({"email": email})
    if user_data:
        return UserInDB(**user_data)
    return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user by ID"""
    users = await get_users_collection()
    try:
        user_data = await users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return UserInDB(**user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")
    return None

async def create_user(user: UserCreate) -> UserInDB:
    """Create new user"""
    users = await get_users_collection()
    
    # Check if email already exists
    if await get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with hashed password
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    try:
        # Insert user
        result = await users.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        
        # Use from_mongo to convert the document
        return UserInDB.from_mongo(user_dict)
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

async def update_user(user_id: str, user_update: UserUpdate) -> UserInDB:
    """Update user"""
    users = await get_users_collection()
    
    # Get current user
    current_user = await get_user_by_id(user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Get updated user
    updated_user = await get_user_by_id(user_id)
    return updated_user

async def delete_user(user_id: str) -> bool:
    """Delete user"""
    users = await get_users_collection()
    result = await users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0

async def list_users(skip: int = 0, limit: int = 100) -> List[User]:
    """List users"""
    users = await get_users_collection()
    cursor = users.find().skip(skip).limit(limit)
    user_list = await cursor.to_list(length=limit)
    return [User(**user) for user in user_list]

async def update_last_login(user_id: str) -> None:
    """Update user's last login"""
    users = await get_users_collection()
    await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login": datetime.utcnow()}}
    )

async def verify_user_credentials(email: str, password: str) -> Optional[UserInDB]:
    """Verify user credentials"""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

