from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Almacenamiento en memoria para rate limiting
rate_limit_store: Dict[str, Tuple[int, datetime]] = {}
login_attempts: Dict[str, Tuple[int, datetime]] = {}

# Rutas excluidas del rate limiting
EXCLUDED_PATHS = [
    "/auth/token",
    "/auth/register",
    "/docs",
    "/redoc",
    "/openapi.json"
]

async def security_middleware(request: Request, call_next):
    # Verificar si la ruta está excluida
    if request.url.path in EXCLUDED_PATHS:
        return await call_next(request)
    
    # Obtener IP del cliente
    client_ip = request.client.host
    
    # Verificar rate limit
    if client_ip in rate_limit_store:
        count, timestamp = rate_limit_store[client_ip]
        if datetime.now() - timestamp < timedelta(minutes=1):
            if count >= 100:  # 100 requests por minuto
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests"}
                )
            rate_limit_store[client_ip] = (count + 1, timestamp)
        else:
            rate_limit_store[client_ip] = (1, datetime.now())
    else:
        rate_limit_store[client_ip] = (1, datetime.now())
    
    # Agregar headers de seguridad
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

async def login_attempt_middleware(request: Request, call_next):
    if request.url.path != "/auth/token":
        return await call_next(request)
    
    client_ip = request.client.host
    
    # Limpiar intentos antiguos
    if client_ip in login_attempts:
        count, timestamp = login_attempts[client_ip]
        if datetime.now() - timestamp > timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW):
            login_attempts[client_ip] = (0, datetime.now())
    
    # Verificar intentos de login
    if client_ip in login_attempts:
        count, timestamp = login_attempts[client_ip]
        if count >= settings.MAX_LOGIN_ATTEMPTS:
            if datetime.now() - timestamp < timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many login attempts. Please try again later."}
                )
            else:
                login_attempts[client_ip] = (1, datetime.now())
        else:
            login_attempts[client_ip] = (count + 1, timestamp)
    else:
        login_attempts[client_ip] = (1, datetime.now())
    
    return await call_next(request)

# Instancias de los middlewares
security_middleware = security_middleware
login_attempt_middleware = login_attempt_middleware 