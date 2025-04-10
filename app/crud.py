from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from app.models import Drink, Ingredient, DrinkIngredient, Pump
from app.schemas import DrinkCreate, IngredientCreate, PumpCreate
from datetime import datetime
from fastapi import HTTPException


###########################
## PARA PRENDER LED ##
import RPi.GPIO as GPIO
import threading
import time
#########################
PUMP_GPIO_MAP = {
    1: 17,
    2: 27,
    3: 23,
    4: 24
}
###########################
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in PUMP_GPIO_MAP.values():
    GPIO.setup(pin, GPIO.OUT)
###########################
###########################


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
async def assign_pump(db: AsyncSession, pump_id: int, pump_data: PumpCreate):
    existing_pump = await db.execute(
        select(Pump).where(Pump.ingredient_id == pump_data.ingredient_id)
    )
    existing_pump = existing_pump.scalars().first()

    if existing_pump and existing_pump.id != pump_id:
        raise HTTPException(status_code=400, detail="Este ingrediente ya está asignado a otro Pump.")

    try:
        # Asegurar que cargamos los datos relacionados
        result = await db.execute(
            select(Pump).options(joinedload(Pump.ingredient)).where(Pump.id == pump_id)
        )
        pump = result.scalars().first()

        if not pump:
            raise HTTPException(status_code=404, detail="Pump no encontrado.")

        pump.ingredient_id = pump_data.ingredient_id
        pump.assigned_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(pump)  # Actualiza los datos en SQLAlchemy

        return pump  # Ahora devuelve el objeto con los datos cargados correctamente

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="No se puede asignar este ingrediente a otro Pump.")
    

"""
# Preparar un trago: verificar disponibilidad de ingredientes
async def prepare_drink_logic(db: AsyncSession, drink_id: int):
    # 1. Buscar el drink y sus ingredientes
    result = await db.execute(
        select(Drink)
        .options(joinedload(Drink.ingredients))
        .where(Drink.id == drink_id)
    )
    drink = result.unique().scalar_one_or_none()


    if not drink:
        raise HTTPException(status_code=404, detail="Drink no encontrado")

    # 2. Obtener las bombas configuradas
    result = await db.execute(select(Pump))
    pumps = result.scalars().all()
    available_ingredient_ids = {pump.ingredient_id for pump in pumps if pump.ingredient_id is not None}


    # 3. Verificar si todos los ingredientes están disponibles
    missing_ingredients = []
    for drink_ingredient in drink.ingredients:
        if drink_ingredient.ingredient_id not in available_ingredient_ids:
            missing_ingredients.append(drink_ingredient.ingredient_id)

    if missing_ingredients:
        raise HTTPException(
            status_code=400,
            detail=f"No están disponibles en las bombas los ingredientes: {missing_ingredients}"
        )

    # 4. Simular preparación (en el futuro acá van los GPIO)
    return {
        "message": f"Preparando el trago: {drink.name}",
        "instructions": [
            {
                "ingredient_id": di.ingredient_id,
                "amount_ml": di.amount_ml
            } for di in drink.ingredients
        ]
    }
"""

def activar_bomba(gpio_pin, tiempo):
    GPIO.output(gpio_pin, GPIO.HIGH)
    time.sleep(tiempo)
    GPIO.output(gpio_pin, GPIO.LOW)

async def prepare_drink_logic(db: AsyncSession, drink_id: int):
    result = await db.execute(
        select(Drink)
        .options(joinedload(Drink.ingredients))
        .where(Drink.id == drink_id)
    )
    drink = result.unique().scalar_one_or_none()

    if not drink:
        raise HTTPException(status_code=404, detail="Drink no encontrado")

    result = await db.execute(select(Pump))
    pumps = result.scalars().all()
    available_ingredient_ids = {pump.ingredient_id for pump in pumps if pump.ingredient_id is not None}

    missing_ingredients = []
    for di in drink.ingredients:
        if di.ingredient_id not in available_ingredient_ids:
            missing_ingredients.append(di.ingredient_id)

    if missing_ingredients:
        raise HTTPException(
            status_code=400,
            detail=f"No están disponibles en las bombas los ingredientes: {missing_ingredients}"
        )

    ingrediente_a_bomba = {pump.ingredient_id: pump.id for pump in pumps if pump.ingredient_id}

    # Ordenar los ingredientes por cantidad ASC (el más chico primero)
    sorted_ingredients = sorted(drink.ingredients, key=lambda x: x.amount_ml)

    def preparar_secuencial():
        for di in sorted_ingredients:
            bomba_id = ingrediente_a_bomba.get(di.ingredient_id)
            gpio_pin = PUMP_GPIO_MAP.get(bomba_id)
            if gpio_pin:
                tiempo = di.amount_ml * 0.1
                activar_bomba(gpio_pin, tiempo)

    threading.Thread(target=preparar_secuencial).start()

    return {
        "message": f"Preparando el trago: {drink.name}",
        "instructions": [
            {
                "ingredient_id": di.ingredient_id,
                "amount_ml": di.amount_ml,
                "pump": ingrediente_a_bomba.get(di.ingredient_id),
                "gpio_pin": PUMP_GPIO_MAP.get(ingrediente_a_bomba.get(di.ingredient_id))
            } for di in sorted_ingredients
        ]
    }