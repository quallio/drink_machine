from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import delete
from app.database import get_db
from app.models import Drink, DrinkIngredient
from app.schemas import DrinkCreate, DrinkResponse
from app.crud import get_drinks, create_drink

## PARA PRENDER LED ##
import RPi.GPIO as GPIO
import threading
import time
#########################
# GPIO 17, 27, 23 y 24 --> bombas 1, 2, 3 y 4
#########################
LED_PIN_17 = 17
LED_PIN_27 = 27
LED_PIN_23 = 23
LED_PIN_24 = 24
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN_17, GPIO.OUT)
GPIO.setup(LED_PIN_27, GPIO.OUT)
GPIO.setup(LED_PIN_23, GPIO.OUT)
GPIO.setup(LED_PIN_24, GPIO.OUT)
#########################



router = APIRouter(prefix="/drinks", tags=["Drinks"])

# Obtener lista de Drinks con sus ingredientes
@router.get("/", response_model=list[DrinkResponse])
async def read_drinks(db: AsyncSession = Depends(get_db)):
    return await get_drinks(db)

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

    # 🔹 Eliminar los registros en drink_ingredients sin tocar ingredients
    await db.execute(delete(DrinkIngredient).where(DrinkIngredient.drink_id == drink_id))

    # 🔹 Eliminar el Drink
    await db.delete(drink)
    await db.commit()

    return {"message": "Drink deleted"}

from app.crud import prepare_drink_logic  # Asegurate de importar esto arriba

# Preparar un drink
@router.post("/prepare/{drink_id}")
async def prepare_drink(drink_id: int, db: AsyncSession = Depends(get_db)):
    return await prepare_drink_logic(db, drink_id)


# Encender los 4 leds. Just testing.
@router.post("/led/{tiempo}")
def encender_led(tiempo: int):
    def encender_leds_durante(t):
        GPIO.output(LED_PIN_17, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(LED_PIN_17, GPIO.LOW)
        GPIO.output(LED_PIN_27, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(LED_PIN_27, GPIO.LOW)
        GPIO.output(LED_PIN_23, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(LED_PIN_23, GPIO.LOW)
        GPIO.output(LED_PIN_24, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(LED_PIN_24, GPIO.LOW)

    thread = threading.Thread(target=encender_leds_durante, args=(tiempo,))
    thread.start()
    return {"mensaje": f"LED encendido por {tiempo} segundos"}

