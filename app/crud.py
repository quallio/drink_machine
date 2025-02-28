from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models import Drink, Ingredient, DrinkIngredient, Pump
from app.schemas import DrinkCreate, IngredientCreate, PumpCreate

# Obtener lista de Drinks con sus ingredientes
async def get_drinks(db: AsyncSession):
    result = await db.execute(
        select(Drink)
        .options(joinedload(Drink.ingredients).joinedload(DrinkIngredient.ingredient))
    )
    return result.unique().scalars().all()  # <--- Agregamos .unique()


# Crear un nuevo Drink con ingredientes asociados
async def create_drink(db: AsyncSession, drink_data: DrinkCreate):
    drink = Drink(name=drink_data.name, description=drink_data.description)
    db.add(drink)
    await db.commit()
    await db.refresh(drink)

    # Agregar los ingredientes a drink_ingredients
    for ingredient_data in drink_data.ingredients:
        drink_ingredient = DrinkIngredient(
            drink_id=drink.id,
            ingredient_id=ingredient_data.ingredient_id,
            amount_ml=ingredient_data.amount_ml
        )
        db.add(drink_ingredient)

    await db.commit()

    # 🔹 IMPORTANTE: Volvemos a obtener el objeto `Drink` con `joinedload()`
    result = await db.execute(
        select(Drink)
        .options(joinedload(Drink.ingredients).joinedload(DrinkIngredient.ingredient))
        .filter(Drink.id == drink.id)
    )
    return result.unique().scalar_one()


# Obtener lista de ingredientes
async def get_ingredients(db: AsyncSession):
    result = await db.execute(select(Ingredient))
    return result.scalars().all()

# Crear un nuevo ingrediente
async def create_ingredient(db: AsyncSession, ingredient_data: IngredientCreate):
    ingredient = Ingredient(name=ingredient_data.name, is_alcoholic=ingredient_data.is_alcoholic)
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient

# Obtener la configuración actual de las bombas
async def get_pumps(db: AsyncSession):
    result = await db.execute(select(Pump).options(joinedload(Pump.ingredient)))
    return result.scalars().all()

# Configurar un ingrediente en una bomba
async def assign_pump(db: AsyncSession, pump_data: PumpCreate):
    pump = await db.get(Pump, pump_data.ingredient_id)
    if pump:
        pump.ingredient_id = pump_data.ingredient_id
    else:
        pump = Pump(ingredient_id=pump_data.ingredient_id)
        db.add(pump)

    await db.commit()
    await db.refresh(pump)
    return pump
