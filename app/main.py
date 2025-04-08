from fastapi import FastAPI
from app.routes.drinks import router as drinks_router
from app.routes.pumps import router as pumps_router
from app.routes.ingredients import router as ingredients_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas con alias
app.include_router(drinks_router)
app.include_router(pumps_router)
app.include_router(ingredients_router)

@app.get("/")
def home():
    return {"message": "Welcome to Drink Machine API!"}
