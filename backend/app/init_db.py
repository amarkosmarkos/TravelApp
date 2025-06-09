from .database import engine
from .models import travel, user

def init_db():
    travel.Base.metadata.create_all(bind=engine)
    user.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.") 