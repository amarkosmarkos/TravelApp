from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import auth, travel, users
from app.services.hotel_suggestions_service import hotel_suggestions_service
from app.database import get_itineraries_collection
import asyncio
from app.middleware.security import security_middleware, login_attempt_middleware
from app.config import settings
from app.database import connect_to_mongodb, close_mongodb_connection
import logging
from datetime import datetime
import json
import uvicorn

# Configurar logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Agregar middlewares de seguridad
app.middleware("http")(security_middleware)
app.middleware("http")(login_attempt_middleware)

# Incluir los routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(travel.router, prefix="/api/travels", tags=["travels"])  # Todo bajo /api/travels
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    duration = datetime.now() - start_time
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration.total_seconds():.2f}s")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/")
async def root():
    return {
        "message": "Welcome to Travel Assistant API",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else None
    }

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Iniciando aplicación...")
    await connect_to_mongodb()
    logger.info("Aplicación iniciada correctamente")
    # Tarea periódica: rellenar hotel_suggestions faltantes
    async def _periodic_fill_hotels():
        while True:
            try:
                itineraries = await get_itineraries_collection()
                cursor = itineraries.find({
                    "$or": [
                        {"hotel_suggestions": {"$exists": False}},
                        {"hotel_suggestions": {"$size": 0}}
                    ]
                }).limit(5)
                async for it in cursor:
                    travel_id = it.get("travel_id")
                    if travel_id:
                        try:
                            await hotel_suggestions_service.generate_and_save_for_travel(travel_id)
                        except Exception as e:
                            logger.error(f"Periodic hotels generation error for {travel_id}: {e}")
            except Exception as e:
                logger.error(f"Periodic hotels scan failed: {e}")
            await asyncio.sleep(60)  # cada 60s

    try:
        asyncio.create_task(_periodic_fill_hotels())
    except Exception as e:
        logger.error(f"Error scheduling periodic hotels task: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info("Cerrando aplicación...")
    await close_mongodb_connection()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
