from fastapi import FastAPI
from app.routes import drinks
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen (puedes restringirlo luego)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)

# Incluir rutas
app.include_router(drinks.router)

@app.get("/")
def home():
    return {"message": "Welcome to Drink Machine API!"}
