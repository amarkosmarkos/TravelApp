from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, chat, travel
from .config import settings

app = FastAPI(title="Travel App API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers sin prefijos adicionales ya que están definidos en los routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(travel.router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Travel App"}
