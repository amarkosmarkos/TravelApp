from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

load_dotenv()

# Si no hay SECRET_KEY en el .env, usar una por defecto para desarrollo
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_por_defecto_para_desarrollo")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Usar OAuth2PasswordBearer para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print(f"Verificando contraseña: {plain_password} contra hash: {hashed_password}")
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """Crea un token de acceso con datos."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")