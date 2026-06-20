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
import asyncio
import time
#########################
PUMP_GPIO_MAP = {
    1: 17,
    2: 27,
    3: 23,
    4: 24
}
# Sensor de presencia de vaso (señal activa en bajo: 0V = vaso presente, 3.3V = sin vaso)
GLASS_SENSOR_PIN = 25
###########################
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in PUMP_GPIO_MAP.values():
    GPIO.setup(pin, GPIO.OUT)
# Entrada con pull-up: si el sensor se desconecta, se lee "sin vaso" (1) en vez de flotante
GPIO.setup(GLASS_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
###########################

# Candado: garantiza que se prepare un solo trago a la vez
prepare_lock = asyncio.Lock()


# Devuelve True si hay un vaso presente (señal en bajo / 0V)
def vaso_presente() -> bool:
    return GPIO.input(GLASS_SENSOR_PIN) == GPIO.LOW


# Constantes de calibración
VOLUME_PER_DRINK = 300   # ml por vaso estándar
FLOW_RATE = 300 / 9      # ml/seg (≈33.33 ml/s)


# Obtener lista de Drinks con sus ingredientes y si están available para ser preparados o no.
async def get_drinks_with_availability(db: AsyncSession):
    result = await db.execute(
        select(Drink)
        .options(joinedload(Drink.ingredients).joinedload(DrinkIngredient.ingredient))
    )
    drinks = result.unique().scalars().all()

    pump_result = await db.execute(select(Pump))
    pumps = pump_result.scalars().all()
    available_ingredient_ids = {pump.ingredient_id for pump in pumps if pump.ingredient_id is not None}

    for drink in drinks:
        ingredient_ids = {di.ingredient_id for di in drink.ingredients}
        drink.is_available = ingredient_ids.issubset(available_ingredient_ids)

    # 🔹 Ordenar: primero disponibles (True), después no disponibles (False)
    drinks.sort(key=lambda d: d.is_available, reverse=True)

    return drinks


# Crear un nuevo Drink con ingredientes asociados
async def create_drink(db: AsyncSession, drink_data: DrinkCreate):
    drink = Drink(name=drink_data.name, description=drink_data.description)
    db.add(drink)
    await db.commit()
    await db.refresh(drink)

    # Agregar los ingredientes con proporciones
    for ingredient_data in drink_data.ingredients:
        drink_ingredient = DrinkIngredient(
            drink_id=drink.id,
            ingredient_id=ingredient_data.ingredient_id,
            proportion=ingredient_data.proportion  # 🔹 antes era amount_ml
        )
        db.add(drink_ingredient)

    await db.commit()

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
        result = await db.execute(
            select(Pump).options(joinedload(Pump.ingredient)).where(Pump.id == pump_id)
        )
        pump = result.scalars().first()

        if not pump:
            raise HTTPException(status_code=404, detail="Pump no encontrado.")

        pump.ingredient_id = pump_data.ingredient_id
        pump.assigned_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(pump)

        return pump

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="No se puede asignar este ingrediente a otro Pump.")


# Apaga todas las bombas (seguridad: que ninguna quede mandando líquido)
def apagar_todas_las_bombas():
    for pin in PUMP_GPIO_MAP.values():
        GPIO.output(pin, GPIO.LOW)


# Activa la bomba durante `tiempo` segundos, pero vigila el vaso mientras tanto.
# Devuelve True si terminó OK, False si se interrumpió porque desapareció el vaso.
def activar_bomba(gpio_pin, tiempo):
    INTERVALO = 0.5  # cada cuánto (seg) se chequea el sensor de vaso
    transcurrido = 0.0
    GPIO.output(gpio_pin, GPIO.HIGH)
    while transcurrido < tiempo:
        if not vaso_presente():
            GPIO.output(gpio_pin, GPIO.LOW)  # corta esta bomba al instante
            return False
        time.sleep(INTERVALO)
        transcurrido += INTERVALO
    GPIO.output(gpio_pin, GPIO.LOW)
    return True


# Preparar un trago con proporciones (secuencial, de menor a mayor)
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

    # 1.5. Rechazar si ya se está preparando otro trago (un solo trago a la vez).
    # El check + acquire son atómicos (sin await en el medio), así no hay carrera.
    if prepare_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Ya se está preparando un trago. Esperá a que termine."
        )

    async with prepare_lock:
        # 1.6. Verificar que haya un vaso presente antes de preparar
        if not vaso_presente():
            raise HTTPException(
                status_code=400,
                detail="No hay vaso presente. Colocá un vaso antes de preparar el trago."
            )

        # 2. Obtener las bombas configuradas
        result = await db.execute(select(Pump))
        pumps = result.scalars().all()
        available_ingredient_ids = {pump.ingredient_id for pump in pumps if pump.ingredient_id is not None}

        # 3. Verificar si todos los ingredientes están disponibles
        missing_ingredients = []
        for di in drink.ingredients:
            if di.ingredient_id not in available_ingredient_ids:
                missing_ingredients.append(di.ingredient_id)

        if missing_ingredients:
            raise HTTPException(
                status_code=400,
                detail=f"No están disponibles en las bombas los ingredientes: {missing_ingredients}"
            )

        # 4. Mapeo ingrediente → bomba
        ingrediente_a_bomba = {pump.ingredient_id: pump.id for pump in pumps if pump.ingredient_id}

        # 5. Ordenar por proporción ascendente (menos cantidad primero)
        sorted_ingredients = sorted(drink.ingredients, key=lambda x: x.proportion)

        # 6. Preparar secuencialmente (uno tras otro).
        # Devuelve True si se completó, False si se interrumpió por falta de vaso.
        def preparar_secuencial():
            for di in sorted_ingredients:
                bomba_id = ingrediente_a_bomba.get(di.ingredient_id)
                gpio_pin = PUMP_GPIO_MAP.get(bomba_id)
                if gpio_pin:
                    ml = di.proportion * VOLUME_PER_DRINK
                    tiempo = ml / FLOW_RATE
                    if not activar_bomba(gpio_pin, tiempo):
                        apagar_todas_las_bombas()  # seguridad: cortar todo
                        return False
            return True

        # Esperar a que termine la preparación antes de responder
        # (corre los time.sleep en un hilo para no bloquear el resto del servidor)
        completado = await asyncio.to_thread(preparar_secuencial)

        # Si se quitó el vaso a mitad de la preparación, avisar y no marcar como listo
        if not completado:
            raise HTTPException(
                status_code=400,
                detail="Se retiró el vaso durante la preparación. Se detuvieron las bombas."
            )

        return {
            "message": f"Trago preparado: {drink.name}",
            "instructions": [
                {
                    "ingredient_id": di.ingredient_id,
                    "proportion": di.proportion,
                    "ml": di.proportion * VOLUME_PER_DRINK,
                    "time_s": (di.proportion * VOLUME_PER_DRINK) / FLOW_RATE,
                    "pump": ingrediente_a_bomba.get(di.ingredient_id),
                    "gpio_pin": PUMP_GPIO_MAP.get(ingrediente_a_bomba.get(di.ingredient_id))
                } for di in sorted_ingredients
            ]
        }
