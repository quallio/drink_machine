from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import delete
from app.database import get_db
from app.schemas import IngredientResponse
from app.crud import get_ingredients


router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

# Obtener lista de Ingredients
@router.get("/", response_model=list[IngredientResponse])
async def read_ingredients(db: AsyncSession = Depends(get_db)):
    return await get_ingredients(db)



