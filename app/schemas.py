from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Esquema para Ingrediente
class IngredientBase(BaseModel):
    name: str
    is_alcoholic: bool

class IngredientCreate(IngredientBase):
    pass

class IngredientResponse(IngredientBase):
    id: int

    class Config:
        from_attributes = True


# Esquema para la relación Drink - Ingredients
class DrinkIngredientBase(BaseModel):
    ingredient_id: int
    proportion: float = Field(..., ge=0, le=1, description="Proporción entre 0 y 1")

class DrinkIngredientCreate(DrinkIngredientBase):
    pass

class DrinkIngredientResponse(DrinkIngredientBase):
    id: int
    ingredient: IngredientResponse

    class Config:
        from_attributes = True


# Esquema para Drink (Trago)
class DrinkBase(BaseModel):
    name: str
    description: str

class DrinkCreate(DrinkBase):
    ingredients: List[DrinkIngredientCreate]

class DrinkResponse(DrinkBase):
    id: int
    ingredients: List[DrinkIngredientResponse]
    is_available: Optional[bool] = None  # <-- Campo opcional agregado

    class Config:
        from_attributes = True


# Esquema para Pumps (Bombas)
class PumpBase(BaseModel):
    ingredient_id: int

class PumpCreate(PumpBase):
    pass

class PumpResponse(PumpBase):
    id: int
    assigned_at: datetime
    ingredient: Optional[IngredientResponse]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Convierte datetime a string ISO 8601
        }
