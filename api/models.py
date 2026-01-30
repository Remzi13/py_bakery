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
    unit_name: Optional[str] = None
    conversion_factor: float = 1.0
    recipe_unit_id: Optional[int] = None
    recipe_unit_name: Optional[str] = None

class ProductBase(BaseModel):
    name: str
    price: float

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
    price: float
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
    default_price: float
    category_id: int
    category_name: Optional[str] = None
    stock: bool = False

class ExpenseCategoryCreate(BaseModel):
    name: str

class ExpenseTypeCreate(BaseModel):
    name: str
    default_price: float
    category_name: str # Use name for creation
    stock: bool = False

class Expense(BaseModel):
    id: Optional[int]
    type_id: int
    name: str
    price: float
    category_id: int
    category_name: Optional[str] = None
    quantity: float
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    date: str

class ExpenseCreate(BaseModel):
    type_id: int
    price: float
    quantity: float
    supplier_id: Optional[int] = None

class ExpenseItemCreate(BaseModel):
    expense_type_id: int
    quantity: float
    price: float
    unit_id: int

class ExpenseDocumentCreate(BaseModel):
    date: str
    supplier_id: int
    comment: Optional[str] = None
    items: List[ExpenseItemCreate]

class ExpenseDocumentResponse(BaseModel):
    id: int
    date: str
    supplier_name: Optional[str]
    total_amount: float
    comment: Optional[str]
    items_count: int

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
    price: float

class OrderResponse(BaseModel):
    id: int
    created_date: str
    completion_date: Optional[str]
    status: str
    additional_info: Optional[str]
    order_items: List[OrderItemResponse]
