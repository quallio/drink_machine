from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import delete
from app.database import get_db
from app.models import Drink, DrinkIngredient
from app.schemas import DrinkCreate, DrinkResponse
from app.crud import get_drinks, create_drink


router = APIRouter(prefix="/drinks", tags=["Drinks"])

# Obtener lista de Drinks con sus ingredientes
@router.get("/", response_model=list[DrinkResponse])
async def read_drinks(db: AsyncSession = Depends(get_db)):
    return await get_drinks(db)

# Crear un nuevo Drink con ingredientes
@router.post("/", response_model=DrinkResponse)
async def add_drink(drink: DrinkCreate, db: AsyncSession = Depends(get_db)):
    return await create_drink(db, drink)

# Eliminar un Drink por ID
@router.delete("/{drink_id}")
async def remove_drink(drink_id: int, db: AsyncSession = Depends(get_db)):
    drink = await db.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")

    # 🔹 Eliminar los registros en drink_ingredients sin tocar ingredients
    await db.execute(delete(DrinkIngredient).where(DrinkIngredient.drink_id == drink_id))

    # 🔹 Eliminar el Drink
    await db.delete(drink)
    await db.commit()

    return {"message": "Drink deleted"}

