from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from ..crud.user import create_user, get_user_by_email, update_user
from ..models.user import User, UserInDB, Token, UserCreate, UserUpdate
from ..utils.authentication import hash_password
from ..dependencies import get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """
    Register a new user.
    """
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create password hash
        hashed_pw = hash_password(user.password)

        # Create user in database
        user_in_db = UserInDB(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_pw,
            is_active=user.is_active,
            permissions=user.permissions,
            roles=user.roles
        )

        created_user = await create_user(user_in_db)
        return created_user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {str(e)}"
        )

@router.get("/profile", response_model=User)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile.
    """
    return current_user

@router.put("/profile", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user profile.
    """
    try:
        updated_user = await update_user(current_user.id, user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.get("/", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_active_user)):
    """
    Get all users (admin only).
    """
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    # TODO: Implement get_users function in crud
    return []

