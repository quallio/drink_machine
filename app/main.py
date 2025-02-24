from fastapi import FastAPI
from app.routes import drinks
from app.database import engine, Base

app = FastAPI()

# Incluir rutas
app.include_router(drinks.router)

@app.get("/")
def home():
    return {"message": "Welcome to Drink Machine API!"}
