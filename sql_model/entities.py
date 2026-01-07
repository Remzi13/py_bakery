from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# --- Структуры данных для использования с базой данных (SQLite) ---

# В dataclass мы теперь храним ID связанных сущностей (int), 
# а не их числовые константы, как раньше.

@dataclass(frozen=True)
class Ingredient:
    """Materials для производства."""
    name: str
    unit_id: int  # Ссылка на ID из таблицы 'units'
    id: Optional[int] = None # ID из БД (PRIMARY KEY), может быть None до сохранения

@dataclass(frozen=True)
class Product:
    """Готовый продукт для продажи."""
    name: str
    price: int
    # Ингредиенты хранятся в отдельной таблице 'product_ingredients'
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass
class StockItem:
    """Инвентарь/Запас (изменяемый)."""
    name: str
    category_id: int # Ссылка на ID из таблицы 'stock_categories'
    quantity: float
    unit_id: int     # Ссылка на ID из таблицы 'units'
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass(frozen=True)
class Sale:
    """Проданный продукт."""
    product_id: int # Ссылка на ID продукта из таблицы 'products'
    product_name: str
    price: int
    quantity: float    
    discount : int # percent
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass(frozen=True)
class ExpenseType:
    """Тип расхода (например, 'Аренда', 'Мука')."""
    name: str
    default_price: int
    category_id: int    # Ссылка на ID из таблицы 'expense_categories'
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass(frozen=True)
class Supplier:
    """Поставщик сырья или услуг."""
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass(frozen=True)
class Expense:
    """Фактический расход, зафиксированный во времени."""
    type_id: int # Ссылка на ID типа расхода
    name: str
    price: int
    category_id: int
    quantity: float
    supplier_id: Optional[int] = None # <-- НОВОЕ ПОЛЕ
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass(frozen=True)
class WriteOff:
    """Запись о списании (готового продукта или сырья/запаса)."""
    quantity: float # <-- Изменили на FLOAT
    reason: str 

    id: Optional[int] = None # ID из БД (PRIMARY KEY)
    # Списание: либо продукт, либо ингредиент/запас (не оба сразу)
    product_id: Optional[int] = None # Ссылка на ID продукта (для готовой продукции)
    stock_item_id: Optional[int] = None # Ссылка на ID StockItem (для сырья, упаковки, оборудования)
    # Дополнительное поле для удобства:
    unit_id: Optional[int] = None # Единица измерения списанного запаса
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

# --- Структуры данных для справочников (новые, для работы с БД) ---

@dataclass(frozen=True)
class Unit:
    """Единица измерения."""
    name: str
    id: Optional[int] = None 

@dataclass(frozen=True)
class StockCategory:
    """Категория запасов."""
    name: str
    id: Optional[int] = None 

@dataclass(frozen=True)
class ExpenseCategory:
    """Категория финансовых расходов."""
    name: str
    id: Optional[int] = None