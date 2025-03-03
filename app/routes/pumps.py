from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Pump
from app.schemas import PumpCreate, PumpResponse
from app.crud import get_pumps, assign_pump
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload



router = APIRouter(prefix="/pumps", tags=["Pumps"])

# Obtener la configuración actual de las bombas
@router.get("/", response_model=List[PumpResponse])
async def read_pumps(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pump).options(joinedload(Pump.ingredient)))
    pumps = result.scalars().all()

    # 🔹 Convertimos assigned_at a string manualmente y agregamos `ingredient_id`
    response = [
        {
            "id": pump.id,
            "ingredient_id": pump.ingredient.id if pump.ingredient else None,  # ✅ Se agrega ingredient_id
            "assigned_at": pump.assigned_at.isoformat() if pump.assigned_at else None,  
            "ingredient": {
                "id": pump.ingredient.id,
                "name": pump.ingredient.name,
                "is_alcoholic": pump.ingredient.is_alcoholic,
            } if pump.ingredient else None
        }
        for pump in pumps
    ]

    return response



# Asignar un ingrediente a una bomba
@router.post("/{pump_id}", response_model=PumpResponse)
async def set_pump(pump_id: int, pump_data: PumpCreate, db: AsyncSession = Depends(get_db)):
    updated_pump = await assign_pump(db, pump_id, pump_data)

    if not updated_pump:
        raise HTTPException(status_code=404, detail="Pump not found")

    return updated_pump
