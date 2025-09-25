from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import delete
from app.database import get_db
from app.models import Drink, DrinkIngredient
from app.schemas import DrinkCreate, DrinkResponse
from app.crud import create_drink, get_drinks_with_availability, prepare_drink_logic

# PARA PRENDER LED
import RPi.GPIO as GPIO
import threading
import time

# GPIO 17, 27, 23 y 24 --> bombas 1, 2, 3 y 4
PUMP_LED_PINS = {
    1: 17,
    2: 27,
    3: 23,
    4: 24
}

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in PUMP_LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

router = APIRouter(prefix="/drinks", tags=["Drinks"])

# ✅ Obtener lista de Drinks con info de disponibilidad
@router.get("/", response_model=list[DrinkResponse])
async def read_drinks(db: AsyncSession = Depends(get_db)):
    return await get_drinks_with_availability(db)

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

    await db.execute(delete(DrinkIngredient).where(DrinkIngredient.drink_id == drink_id))
    await db.delete(drink)
    await db.commit()

    return {"message": "Drink deleted"}

# Preparar un drink
@router.post("/prepare/{drink_id}")
async def prepare_drink(drink_id: int, db: AsyncSession = Depends(get_db)):
    return await prepare_drink_logic(db, drink_id)

# Testea las salidas (los 4 leds)
@router.post("/test-leds/{tiempo}")
def test_leds(tiempo: int):
    def encender_leds():
        for pump_id in sorted(PUMP_LED_PINS):
            GPIO.output(PUMP_LED_PINS[pump_id], GPIO.HIGH)
            time.sleep(tiempo)
            GPIO.output(PUMP_LED_PINS[pump_id], GPIO.LOW)

    thread = threading.Thread(target=encender_leds)
    thread.start()
    return {"mensaje": f"Probando LEDs por {tiempo} segundos cada uno"}


# Modo limpieza: acciona todas las bombas 5s cada una
@router.post("/limpieza")
def limpieza():
    # Ejecuta secuencialmente las 4 bombas por 5s cada una
    for pump_id in sorted(PUMP_LED_PINS):
        GPIO.output(PUMP_LED_PINS[pump_id], GPIO.HIGH)
        time.sleep(5)
        GPIO.output(PUMP_LED_PINS[pump_id], GPIO.LOW)

    # Devuelve respuesta solo cuando todo terminó
    return {"message": "✅ Limpieza completada"}
