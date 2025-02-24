from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import DrinkCreate, DrinkResponse
from app.crud import get_drinks, create_drink, delete_drink
from typing import List

router = APIRouter(prefix="/drinks", tags=["Drinks"])

@router.get("/", response_model=List[DrinkResponse])
async def read_drinks(db: AsyncSession = Depends(get_db)):
    return await get_drinks(db)

@router.post("/", response_model=DrinkResponse)
async def add_drink(drink: DrinkCreate, db: AsyncSession = Depends(get_db)):
    return await create_drink(db, drink)

@router.delete("/{drink_id}")
async def remove_drink(drink_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_drink(db, drink_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Drink not found")
    return {"message": "Drink deleted"}
