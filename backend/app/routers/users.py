from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from ..crud.user import create_user, get_user_by_email
from ..models.user import User, UserInDB, Token, UserCreate
from ..utils.authentication import hash_password, verify_password, create_access_token, verify_jwt_token
from fastapi.security import OAuth2PasswordRequestForm
from ..dependencies import oauth2_scheme



# Crear el router con un prefijo
router = APIRouter(
    prefix="/users",  # Prefijo para todas las rutas de este router
    tags=["users"]    # Etiqueta opcional para documentación
)

@router.post("/register")
async def register_user(user: User):
    try:
        print(f"Received user data: {user.dict()}")

        # Validar datos básicos
        if not user.email or not user.name or not user.password:
            raise HTTPException(
                status_code=400,
                detail="Email, name and password are required"
            )

        # Verificar si el usuario ya existe
        existing_user = await get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Crear hash de la contraseña
        hashed_pw = hash_password(user.password)
        print(f"Password hashed successfully")

        # Crear usuario en la base de datos
        user_in_db = UserInDB(
            email=user.email,
            name=user.name,
            hashed_password=hashed_pw
        )
        print(f"Creating user in DB: {user_in_db.dict()}")

        user_id = await create_user(user_in_db)
        print(f"User created successfully with ID: {user_id}")

        return {
            "message": "User registered successfully",
            "user": {
                "email": user.email,
                "name": user.name,
                "id": user_id
            }
        }

    except HTTPException as he:
        print(f"HTTP Exception during registration: {str(he)}")
        raise he
    except Exception as e:
        print(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error registering user: {str(e)}"
        )

@router.post("/logout")
async def logout():
    # Logout normalmente se maneja a nivel cliente, pero puedes invalidar tokens aquí
    return {"message": "Logged out"}

@router.get("/profile")
async def get_user_profile(token: str = Depends(oauth2_scheme)):
    try:
        email = verify_jwt_token(token)  # Verificamos y extraemos el email del token
        user = await get_user_by_email(email)  # Buscamos al usuario por su email
        if user:
            return {"name": user["name"], "email": user["email"]}  # Accedemos a los campos como diccionario
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        print(f"Error in profile endpoint: {str(e)}")  # Añadimos logging para debug
        raise HTTPException(status_code=401, detail="Invalid or expired token")

