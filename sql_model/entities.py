from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# --- Структуры данных для использования с базой данных (SQLite) ---

# В dataclass мы теперь храним ID связанных сущностей (int), 
# а не их числовые константы, как раньше.

@dataclass(frozen=True)
class Product:
    """Готовый продукт для продажи."""
    name: str
    price: float
    # Ингредиенты хранятся в отдельной таблице 'product_stock'
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
    price: float
    quantity: float    
    discount : int # percent
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    id: Optional[int] = None # ID из БД (PRIMARY KEY)

@dataclass(frozen=True)
class ExpenseType:
    """Тип расхода (например, 'Аренда', 'Мука')."""
    name: str
    default_price: float
    category_id: int    # Ссылка на ID из таблицы 'expense_categories'
    stock: bool = False # Хранить на складе или нет
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
    price: float
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

@dataclass
class Order:
    """Заказ с отложенным выполнением."""
    created_date: str
    status: str  # 'pending' or 'completed'
    completion_date: Optional[str] = None
    additional_info: Optional[str] = None
    id: Optional[int] = None

@dataclass
class OrderItem:
    """Позиция в заказе."""
    order_id: int
    product_id: int
    product_name: str
    quantity: float
    price: float
    id: Optional[int] = None

@dataclass
class ExpenseDocument:
    """Документ о закупке (чек/накладная)."""
    date: str
    supplier_id: int
    total_amount: float
    comment: Optional[str] = None
    id: Optional[int] = None

@dataclass
class ExpenseItem:
    """Позиция в документе о закупке."""
    document_id: int
    expense_type_id: int
    stock_item_id: Optional[int] # Может быть NULL, если это не складская позиция
    unit_id: int
    quantity: float
    price_per_unit: float
    total_price: float
    id: Optional[int] = None
