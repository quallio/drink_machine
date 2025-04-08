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
RED_LED_PIN = 17
WHITE_LED_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(WHITE_LED_PIN, GPIO.OUT)
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


# Encender LEDs un tiempo x
@router.post("/led/{tiempo}")
def encender_led(tiempo: int):
    def encender_led_durante(t):
        GPIO.output(RED_LED_PIN, GPIO.HIGH)
        time.sleep(t)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        GPIO.output(WHITE_LED_PIN, GPIO.HIGH)
        time.sleep(t*2)
        GPIO.output(WHITE_LED_PIN, GPIO.LOW)

    thread = threading.Thread(target=encender_led_durante, args=(tiempo,))
    thread.start()
    return {"mensaje": f"LED encendido por {tiempo} segundos"}
