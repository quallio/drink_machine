from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla de Drinks (Tragos)
class Drink(Base):
    __tablename__ = "drinks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    
    ingredients = relationship("DrinkIngredient", back_populates="drink")

# Tabla de Ingredients (Ingredientes posibles)
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_alcoholic = Column(Boolean, nullable=False, default=False)

    drinks = relationship("DrinkIngredient", back_populates="ingredient")

# Tabla intermedia Drink_Ingredients (Relación Tragos - Ingredientes)
class DrinkIngredient(Base):
    __tablename__ = "drink_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    drink_id = Column(Integer, ForeignKey("drinks.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    amount_ml = Column(Integer, nullable=False)

    drink = relationship("Drink", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="drinks")

# Tabla Pumps (Qué ingredientes están en las bombas)
class Pump(Base):
    __tablename__ = "pumps"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="SET NULL"), unique=True)
    assigned_at = Column(TIMESTAMP, server_default=func.now())

    ingredient = relationship("Ingredient")
