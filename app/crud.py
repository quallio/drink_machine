from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Drink
from app.schemas import DrinkCreate

async def get_drinks(db: AsyncSession):
    result = await db.execute(select(Drink))
    return result.scalars().all()

async def create_drink(db: AsyncSession, drink: DrinkCreate):
    new_drink = Drink(name=drink.name, description=drink.description)
    db.add(new_drink)
    await db.commit()
    await db.refresh(new_drink)
    return new_drink

async def delete_drink(db: AsyncSession, drink_id: int):
    drink = await db.get(Drink, drink_id)
    if drink:
        await db.delete(drink)
        await db.commit()
    return drink
