from pydantic import BaseModel
from typing import List, Optional

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
    amount_ml: int

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

    class Config:
        from_attributes = True

# Esquema para Pumps (Bombas)
class PumpBase(BaseModel):
    ingredient_id: int

class PumpCreate(PumpBase):
    pass

class PumpResponse(PumpBase):
    id: int
    assigned_at: str
    ingredient: Optional[IngredientResponse]

    class Config:
        from_attributes = True
