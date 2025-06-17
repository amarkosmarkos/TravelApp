# settings.py
from pydantic_settings import BaseSettings
from openai import AzureOpenAI
import os
from typing import Optional, List
from dotenv import load_dotenv
import secrets

# Cargar variables de entorno
load_dotenv()

class Settings(BaseSettings):
    # Información de la aplicación
    PROJECT_NAME: str = "Travel Assistant"
    PROJECT_DESCRIPTION: str = "API para la aplicación de asistente de viajes"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configuración del servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Configuración de la base de datos
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017").rstrip('/')
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "travel_app")
    
    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Configuración de contraseñas
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 100
    
    # Configuración de rate limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_ATTEMPT_WINDOW: int = int(os.getenv("LOGIN_ATTEMPT_WINDOW", "15"))
    
    # Configuración de CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend en desarrollo
        "http://localhost:8000",  # Backend en desarrollo
        "https://travel-assistant.com"  # Producción
    ]
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Servicios externos
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Configuración de rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    
    # API settings
    API_V1_STR: str = "/api"
    
    # WebSocket settings
    WS_URL: str = "ws://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables de entorno no definidas en el modelo

# Instantiate settings (reads from .env or environment)
settings = Settings()

# Validate critical settings for auth
required_auth = [
    settings.MONGODB_URL,
    settings.SECRET_KEY
]
if not all(required_auth):
    missing = [name for name, value in [
        ("MONGODB_URL", settings.MONGODB_URL),
        ("SECRET_KEY", settings.SECRET_KEY)
    ] if not value]
    raise RuntimeError(f"Missing required authentication settings: {', '.join(missing)}")

# Validate Azure settings
required_azure = [
    settings.AZURE_OPENAI_API_KEY,
    settings.AZURE_OPENAI_ENDPOINT,
    settings.AZURE_OPENAI_DEPLOYMENT_NAME
]
if not all(required_azure):
    missing = [name for name, value in [
        ("AZURE_OPENAI_API_KEY", settings.AZURE_OPENAI_API_KEY),
        ("AZURE_OPENAI_ENDPOINT", settings.AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_DEPLOYMENT_NAME", settings.AZURE_OPENAI_DEPLOYMENT_NAME)
    ] if not value]
    raise RuntimeError(f"Missing required Azure settings: {', '.join(missing)}") 