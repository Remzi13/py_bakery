import uuid
from datetime import datetime
from dataclasses import dataclass, field

from typing import List, Dict, Any
# --- Структуры данных (Refactored to dataclasses) ---

# Вложенные классы вынесены на верхний уровень для чистоты и удобства
# (frozen=True делает объект неизменяемым после создания)

@dataclass(frozen=True)
class Ingredient:
    """Сырье для производства."""
    name: str
    unit: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Product:
    """Готовый продукт для продажи."""
    name: str
    price: int
    ingredients: List[Dict[str, Any]]  # Список ингредиентов с их количеством
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Inventory:
    """Инвентарь/Запас (изменяемый)."""
    name: str
    category: int
    quantity: float 
    inv_id: uuid.UUID

@dataclass(frozen=True)
class Sale:
    """Проданный продукт."""
    product_name: str
    price: int
    quantity: float
    product_id: uuid.UUID
    # Используем field(default_factory) для генерации даты по умолчанию
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

@dataclass(frozen=True)
class ExpenseType:
    """Тип расхода (например, 'Аренда', 'Мука')."""
    name: str
    default_price: int
    category: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Expense:
    """Фактический расход, зафиксированный во времени."""
    name: str
    price: int
    category: int
    quantity: float
    type_id: uuid.UUID
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class Category:
    INGREDIENT = 0
    ENVIRONMENT = 1
    PAYMENT = 2

CATEGORY_NAMES = ['ингредиенты', 'оборудование', 'платежи']
