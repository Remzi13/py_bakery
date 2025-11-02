import uuid
from datetime import datetime
from dataclasses import dataclass, field

from typing import List, Dict, Any
# --- Структуры данных (Refactored to dataclasses) ---

# Вложенные классы вынесены на верхний уровень для чистоты и удобства
# (frozen=True делает объект неизменяемым после создания)

class Unit:
    Kilogram    = 0
    Gramm       = 1
    Liter       = 2
    Piece       = 3


@dataclass(frozen=True)
class Ingredient:
    """Сырье для производства."""
    name: str
    unit: Unit
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Product:
    """Готовый продукт для продажи."""
    name: str
    price: int
    ingredients: List[Dict[str, Any]]  # Список ингредиентов с их количеством
    id: uuid.UUID = field(default_factory=uuid.uuid4)

class StockCategory:
    """Категории для учета физического запаса на складе (StockItem)."""
    INGREDIENT  = 0
    PACKAGING   = 1
    EQUIPMENT   = 2 

STOCK_CATEGORY_NAMES = {
    StockCategory.INGREDIENT: 'Сырье',
    StockCategory.PACKAGING:  'Упаковка',
    StockCategory.EQUIPMENT:  'Оборудование'
}

@dataclass
class StockItem:
    """Инвентарь/Запас (изменяемый)."""
    name: str
    category: StockCategory
    quantity: float
    unit: Unit 
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Sale:
    """Проданный продукт."""
    product_name: str
    price: int
    quantity: float
    product_id: uuid.UUID
    discount : int # percent
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

class ExpenseCategory:
    """Категории для учета финансовых расходов (Expense/ExpenseType)."""
    INGREDIENT  = 0
    EQUIPMENT   = 1
    PAYMENT     = 2
    OTHER       = 3

EXPENSE_CATEGORY_NAMES = {
    ExpenseCategory.INGREDIENT: 'Сырьё',
    ExpenseCategory.EQUIPMENT:  'Оборудование',
    ExpenseCategory.PAYMENT:    'Платежи',
    ExpenseCategory.OTHER:      'Другое',
}

@dataclass(frozen=True)
class ExpenseType:
    """Тип расхода (например, 'Аренда', 'Мука')."""
    name: str
    default_price: int
    category: ExpenseCategory
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Expense:
    """Фактический расход, зафиксированный во времени."""
    name: str
    price: int
    category: ExpenseCategory
    quantity: float
    type_id: uuid.UUID
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


UNIT_NAMES = {
    Unit.Kilogram:  'кг',
    Unit.Gramm:     'грамм',
    Unit.Liter:     'литр',
    Unit.Piece:     'штук'
}

def unit_by_name(unit_name: str) -> Unit:
        
    for unit_value, name in UNIT_NAMES.items():        
        if name == unit_name:    
            return unit_value
                
    raise ValueError(f"Единица измерения '{unit_name}' не найдена в UNIT_NAME.")

def category_by_name(category_name : str) -> ExpenseCategory:
    for category, name in EXPENSE_CATEGORY_NAMES.items():
        if name == category_name:    
            return category
        
    raise ValueError(f"Категория '{category_name}' не найдена в EXPENSE_CATEGORY_NAMES.")