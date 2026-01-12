from pydantic import BaseModel
from typing import List, Optional

# --- Shared Models ---

class Unit(BaseModel):
    id: Optional[int]
    name: str

class Ingredient(BaseModel):
    id: Optional[int]
    name: str
    unit_id: int

# --- Product Models ---

class ProductIngredient(BaseModel):
    name: str
    quantity: float
    unit: Optional[str] = None

class ProductBase(BaseModel):
    name: str
    price: int

class ProductCreate(ProductBase):
    materials: List[ProductIngredient]

class ProductResponse(ProductBase):
    id: int
    materials: List[ProductIngredient] = []
# --- Stock Models ---

class StockItem(BaseModel):
    id: Optional[int]
    name: str
    category_id: int
    category_name: Optional[str] = None
    quantity: float
    unit_id: int
    unit_name: Optional[str] = None

class StockCreate(BaseModel):
    name: str
    category_name: str
    quantity: float
    unit_name: str

class StockUpdate(BaseModel):
    quantity_delta: float

class StockSet(BaseModel):
    quantity: float

# --- Sales Models ---

class Sale(BaseModel):
    id: Optional[int]
    product_id: int
    product_name: str
    price: int
    quantity: float
    discount: int
    date: str

class SaleCreate(BaseModel):
    product_id: int
    quantity: float
    discount: int = 0

# --- Expenses Models ---

class ExpenseType(BaseModel):
    id: Optional[int]
    name: str
    default_price: int
    category_id: int
    category_name: Optional[str] = None

class Expense(BaseModel):
    id: Optional[int]
    type_id: int
    name: str
    price: int
    category_id: int
    category_name: Optional[str] = None
    quantity: float
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    date: str

class ExpenseCreate(BaseModel):
    type_id: int
    price: int
    quantity: float
    supplier_id: Optional[int] = None

# --- Supplier Models ---

class Supplier(BaseModel):
    id: Optional[int] = None
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]

# --- Orders Models ---

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    completion_date: Optional[str] = None
    additional_info: Optional[str] = None
    complete_now: bool = False

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: float
    price: int

class OrderResponse(BaseModel):
    id: int
    created_date: str
    completion_date: Optional[str]
    status: str
    additional_info: Optional[str]
    items: List[OrderItemResponse]
