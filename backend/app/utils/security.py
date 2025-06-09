from typing import Optional, Dict, Any, Union
import hashlib
import secrets
import string
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
import logging
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar contraseña
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Contraseña hasheada
    
    Returns:
        bool: True si la contraseña coincide
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Obtener hash de contraseña
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        str: Hash de la contraseña
    """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear token de acceso
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración
    
    Returns:
        str: Token JWT
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verificar token JWT
    
    Args:
        token: Token JWT
    
    Returns:
        Dict[str, Any]: Datos del token
    
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_current_user(token: str = Security(oauth2_scheme)) -> Dict[str, Any]:
    """
    Obtener usuario actual
    
    Args:
        token: Token JWT
    
    Returns:
        Dict[str, Any]: Datos del usuario
    
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"user_id": user_id, "token_data": payload}
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def generate_reset_token(email: str) -> str:
    """
    Generar token de reseteo
    
    Args:
        email: Email del usuario
    
    Returns:
        str: Token de reseteo
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def verify_reset_token(token: str) -> Optional[str]:
    """
    Verificar token de reseteo
    
    Args:
        token: Token de reseteo
    
    Returns:
        Optional[str]: Email del usuario o None si el token es inválido
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token["sub"]
    except jwt.JWTError:
        return None

def generate_verification_token(email: str) -> str:
    """
    Generar token de verificación
    
    Args:
        email: Email del usuario
    
    Returns:
        str: Token de verificación
    """
    delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def verify_verification_token(token: str) -> Optional[str]:
    """
    Verificar token de verificación
    
    Args:
        token: Token de verificación
    
    Returns:
        Optional[str]: Email del usuario o None si el token es inválido
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token["sub"]
    except jwt.JWTError:
        return None

def generate_api_key() -> str:
    """
    Generar API key
    
    Returns:
        str: API key
    """
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """
    Hashear API key
    
    Args:
        api_key: API key en texto plano
    
    Returns:
        str: Hash de la API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verificar API key
    
    Args:
        plain_api_key: API key en texto plano
        hashed_api_key: API key hasheada
    
    Returns:
        bool: True si la API key coincide
    """
    return hash_api_key(plain_api_key) == hashed_api_key

def generate_password_reset_token(email: str) -> str:
    """
    Generar token para restablecer contraseña
    
    Args:
        email: Email del usuario
    
    Returns:
        str: Token para restablecer contraseña
    """
    delta = timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verificar token para restablecer contraseña
    
    Args:
        token: Token para restablecer contraseña
    
    Returns:
        Optional[str]: Email del usuario si el token es válido
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token["sub"]
    except jwt.PyJWTError:
        return None

def generate_email_verification_token(email: str) -> str:
    """
    Generar token para verificar email
    
    Args:
        email: Email del usuario
    
    Returns:
        str: Token para verificar email
    """
    delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verificar token para verificar email
    
    Args:
        token: Token para verificar email
    
    Returns:
        Optional[str]: Email del usuario si el token es válido
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token["sub"]
    except jwt.PyJWTError:
        return None

def generate_csrf_token() -> str:
    """
    Generar token CSRF
    
    Returns:
        str: Token CSRF
    """
    return secrets.token_urlsafe(32)

def verify_csrf_token(token: str, stored_token: str) -> bool:
    """
    Verificar token CSRF
    
    Args:
        token: Token a verificar
        stored_token: Token almacenado
    
    Returns:
        bool: True si coinciden
    """
    return secrets.compare_digest(token, stored_token)

def generate_session_id() -> str:
    """
    Generar ID de sesión
    
    Returns:
        str: ID de sesión
    """
    return secrets.token_urlsafe(32)

def generate_otp() -> str:
    """
    Generar código OTP
    
    Returns:
        str: Código OTP
    """
    return secrets.randbelow(1000000).zfill(6)

def verify_otp(otp: str, stored_otp: str) -> bool:
    """
    Verificar código OTP
    
    Args:
        otp: Código a verificar
        stored_otp: Código almacenado
    
    Returns:
        bool: True si coinciden
    """
    return secrets.compare_digest(otp, stored_otp)

def generate_recovery_code() -> str:
    """
    Generar código de recuperación
    
    Returns:
        str: Código de recuperación
    """
    return secrets.token_urlsafe(16)

def verify_recovery_code(code: str, stored_code: str) -> bool:
    """
    Verificar código de recuperación
    
    Args:
        code: Código a verificar
        stored_code: Código almacenado
    
    Returns:
        bool: True si coinciden
    """
    return secrets.compare_digest(code, stored_code) 