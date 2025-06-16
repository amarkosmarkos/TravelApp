from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from ..models.user import User, TokenData
from ..database import get_database
from ..config import settings
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# Configuración de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Códigos de error WebSocket
WEBSOCKET_ERRORS = {
    4001: "No token provided",
    4002: "Invalid token",
    4003: "Token expired",
    4004: "Travel not found or unauthorized",
    1011: "Internal server error"
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT con los datos proporcionados."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_database)) -> User:
    """Obtiene el usuario actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Buscar el usuario en la base de datos
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise credentials_exception
            
        return User(**user)
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception

async def verify_ws_token(token: str) -> str:
    """Verifica el token para conexiones WebSocket y devuelve el ID del usuario."""
    logger.info("=== WebSocket Token Verification ===")
    logger.info(f"Token received: {token[:20]}...")
    
    try:
        # Decodificar el token
        logger.info("Decoding token...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        logger.info(f"Token payload: {payload}")
        
        if user_id is None:
            logger.error("No user_id (sub) in token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token"
            )
        
        # Verificar expiración
        exp = payload.get("exp")
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            now = datetime.utcnow()
            logger.info(f"Token expiration: {exp_time}, Current time: {now}")
            if now > exp_time:
                logger.error("Token expired")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token expired"
                )
        
        # Buscar el usuario
        logger.info(f"Looking up user with ID: {user_id}")
        db = await get_database()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            logger.error(f"User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found"
            )
        
        logger.info(f"User found: {user.get('email')}")
        # Devolver solo el ID del usuario como string
        return str(user_id)
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )
    finally:
        logger.info("=== WebSocket Token Verification End ===")

async def verify_travel_access(travel_id: str, user_id: str, db) -> bool:
    """Verifica que el usuario tiene acceso al viaje."""
    try:
        # Convertir travel_id a ObjectId
        travel_object_id = ObjectId(travel_id)
        
        # Buscar el viaje
        travel = await db.travels.find_one({"_id": travel_object_id})
        
        if not travel:
            logger.error(f"Travel {travel_id} not found")
            return False
            
        # Asegurarnos de que ambos IDs son strings
        travel_user_id = str(travel.get("user_id"))
        user_id_str = str(user_id)
            
        # Comparación exacta de strings
        if travel_user_id != user_id_str:
            logger.error(f"User {user_id_str} is not the owner of travel {travel_id}. Travel owner: {travel_user_id}")
            return False
            
        logger.info(f"Access verified for user {user_id_str} to travel {travel_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying travel access: {str(e)}")
        return False 