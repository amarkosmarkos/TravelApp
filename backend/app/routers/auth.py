from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta

from app.core.auth import (
    create_access_token,
    get_current_user,
    get_current_active_user,
    check_permissions
)
from app.models.user import User, UserCreate, UserUpdate
from app.crud.user import (
    create_user,
    get_user_by_email,
    update_user,
    list_users,
    update_last_login,
    verify_user_credentials
)
from app.config import settings
import logging

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login para obtener token de acceso"""
    user = await verify_user_credentials(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último login
    await update_last_login(str(user.id))
    
    # Crear token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "scopes": user.permissions},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    """Registrar nuevo usuario"""
    # Verificar si el email ya existe
    if await get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Crear usuario
    db_user = await create_user(user)
    return db_user

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Obtener información del usuario actual"""
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar información del usuario actual"""
    updated_user = await update_user(str(current_user.id), user_update)
    return updated_user

@router.get("/users", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """Listar usuarios (solo admin)"""
    if "manage_users" not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    users = await list_users(skip=skip, limit=limit)
    return users 