from pydantic import BaseModel
from typing import Dict

class DrinkCreate(BaseModel):
    name: str
    description: str
    ingredients: Dict[str, int]  # Representa el JSON de ingredientes

class DrinkResponse(DrinkCreate):
    id: int

    class Config:
        orm_mode = True
