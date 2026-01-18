# 🔧 Руководство разработчика - API и примеры

## Оглавление
1. [Архитектура проекта](#архитектура-проекта)
2. [Работа с репозиториями](#работа-с-репозиториями)
3. [Примеры CRUD операций](#примеры-crud-операций)
4. [Работа с FastAPI роутерами](#работа-с-fastapi-роутерами)
5. [Частые сценарии](#частые-сценарии)
6. [Отладка и логирование](#отладка-и-логирование)

---

## Архитектура проекта

### Слои приложения

```
main.py (FastAPI приложение)
    ↓
api/routers/ (API endpoints)
    ↓
repositories/ (Бизнес-логика, доступ к данным)
    ↓
sql_model/ (ORM модели)
    ↓
sqlite database (bakery_management.db)
```

### Структура папок

```
py_bakery/
├── main.py                          # FastAPI приложение
├── sql_model/
│   ├── database.py                 # Конфигурация БД
│   ├── entities.py                 # Модели SQLAlchemy
│   └── model.py                    # Главный класс Model (facade)
├── repositories/                    # Бизнес-логика
│   ├── products.py
│   ├── stock.py
│   ├── sales.py
│   ├── suppliers.py
│   ├── orders.py
│   ├── expense_types.py
│   ├── expense_documents.py
│   ├── write_offs.py
│   └── utils.py
├── api/
│   ├── models.py                   # Pydantic модели для API
│   ├── dependencies.py             # FastAPI dependencies
│   └── routers/                    # Маршруты
│       ├── products.py
│       ├── stock.py
│       ├── sales.py
│       ├── suppliers.py
│       ├── orders.py
│       ├── expenses.py
│       └── dashboard.py
├── templates/                       # HTML шаблоны
├── static/                          # CSS, JS
└── tests/                           # Тесты
```

---

## Работа с репозиториями

### Основная идея

Репозиторий - это класс, который:
- Инкапсулирует логику работы с одной сущностью
- Предоставляет методы CRUD (Create, Read, Update, Delete)
- Содержит сложные бизнес-логику запросы

### Пример репозитория: ProductsRepository

```python
# repositories/products.py
from sqlalchemy.orm import Session
from sql_model.entities import Product

class ProductsRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # CREATE
    def create(self, name: str, price: float) -> Product:
        """Создать новый продукт."""
        product = Product(name=name, price=price)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    # READ
    def get_by_id(self, product_id: int) -> Product | None:
        """Получить продукт по ID."""
        return self.db.query(Product).filter_by(id=product_id).first()
    
    def get_by_name(self, name: str) -> Product | None:
        """Получить продукт по имени."""
        return self.db.query(Product).filter_by(name=name).first()
    
    def get_all(self) -> list[Product]:
        """Получить все продукты."""
        return self.db.query(Product).all()
    
    # UPDATE
    def update(self, product_id: int, name: str, price: float) -> Product:
        """Обновить продукт."""
        product = self.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        product.name = name
        product.price = price
        self.db.commit()
        self.db.refresh(product)
        return product
    
    # DELETE
    def delete(self, name: str) -> bool:
        """Удалить продукт по имени."""
        product = self.get_by_name(name)
        if not product:
            raise ValueError(f"Product {name} not found")
        
        self.db.delete(product)
        self.db.commit()
        return True
```

### Шаблон для создания нового репозитория

```python
# repositories/new_entity.py
from sqlalchemy.orm import Session
from sql_model.entities import NewEntity

class NewEntityRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> NewEntity:
        """Создать новую запись."""
        entity = NewEntity(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_all(self) -> list[NewEntity]:
        """Получить все записи."""
        return self.db.query(NewEntity).all()
    
    def get_by_id(self, entity_id: int) -> NewEntity | None:
        """Получить запись по ID."""
        return self.db.query(NewEntity).filter_by(id=entity_id).first()
    
    def update(self, entity_id: int, **kwargs) -> NewEntity:
        """Обновить запись."""
        entity = self.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Удалить запись."""
        entity = self.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        self.db.delete(entity)
        self.db.commit()
        return True
```

---

## Примеры CRUD операций

### 1. Работа с продуктами

```python
from sql_model.model import SQLAlchemyModel

model = SQLAlchemyModel()

# CREATE - создать продукт
product = model.products().create("Батон", 250)
print(f"Создан: {product.name}, ID: {product.id}")

# READ - получить продукт
found = model.products().get_by_id(product.id)
print(f"Найден: {found.name}")

# UPDATE - обновить продукт
updated = model.products().update(product.id, "Батон белый", 300)
print(f"Обновлен: {updated.name}, цена: {updated.price}")

# DELETE - удалить продукт
deleted = model.products().delete("Батон белый")
print(f"Удален: {deleted}")

model.close()
```

### 2. Работа со складом

```python
# CREATE - добавить запас
stock = model.stock().create(
    name="Мука пшеничная",
    category="Materials",
    quantity=50.0,
    unit="kg"
)

# READ - получить запас
stock_item = model.stock().get_by_name("Мука пшеничная")

# UPDATE - изменить количество
updated = model.stock().update_quantity("Мука пшеничная", 45.0)

# Проверить, можно ли удалить
can_delete = model.stock().can_delete("Мука пшеничная")
print(f"Можно удалить: {can_delete}")

# DELETE (если не используется)
if can_delete:
    model.stock().delete("Мука пшеничная")
```

### 3. Работа с продажами

```python
# CREATE - добавить продажу
sale = model.sales().create(
    product_id=1,
    product_name="Батон",
    price=250,
    quantity=5,
    discount=10,  # скидка 10%
    date="2024-01-15"
)

# READ - получить продажи за период
sales = model.sales().get_by_date("2024-01-01", "2024-01-31")
for sale in sales:
    print(f"{sale.product_name}: {sale.quantity} × {sale.price}")

# Получить общий доход
income = model.calculate_income()
print(f"Общий доход: {income}")
```

### 4. Работа с расходами (документы и позиции)

```python
# CREATE - создать документ (счет)
doc = model.expense_documents().create(
    date="2024-01-15",
    supplier_id=1,  # ID поставщика
    total_amount=1000.0,
    comment="Закупка мучных изделий"
)

# Добавить позицию в документ
item = model.expense_documents().add_item(
    document_id=doc.id,
    expense_type_id=1,           # ID типа расхода (например, "Мука")
    stock_item_id=1,             # ID товара на складе (если это товар)
    quantity=50.0,
    price_per_unit=20.0
)

# READ - получить документ
doc = model.expense_documents().get_by_id(1)
print(f"Документ от {doc.supplier.name}: {doc.total_amount}")

# Получить все позиции в документе
items = doc.items
for item in items:
    print(f"  - {item.expense_type.name}: {item.quantity} {item.unit.name} × {item.price_per_unit}")

# DELETE - удалить документ (удалит и все позиции)
model.expense_documents().delete(doc.id)
```

### 5. Работа с заказами

```python
from datetime import datetime

# CREATE - создать заказ
order = model.orders().create(
    created_date=datetime.now().strftime("%Y-%m-%d"),
    status="pending"
)

# Добавить позицию в заказ
order_item = model.orders().add_item(
    order_id=order.id,
    product_id=1,
    product_name="Батон",
    quantity=50,
    price=250
)

# READ - получить заказ
order = model.orders().get_by_id(1)
print(f"Заказ #{order.id} создан {order.created_date}")
for item in order.items:
    print(f"  - {item.product_name}: {item.quantity} шт")

# UPDATE - отметить как выполненный
order = model.orders().mark_completed(order.id, "2024-01-20")

# Получить все ожидающие заказы
pending = model.orders().get_pending()
```

### 6. Работа со списаниями

```python
# CREATE - списать готовый продукт
writeoff = model.writeoffs().create(
    product_id=1,
    quantity=5,
    reason="Брак при производстве",
    date="2024-01-15"
)

# CREATE - списать сырье со склада
writeoff = model.writeoffs().create(
    stock_item_id=1,
    quantity=2.5,
    reason="Подмокла, испортилась",
    date="2024-01-15"
)

# READ - получить все списания
writeoffs = model.writeoffs().get_all()
for wo in writeoffs:
    if wo.product_id:
        print(f"Списано продукта: {wo.quantity}")
    else:
        print(f"Списано материала: {wo.quantity}")
```

---

## Работа с FastAPI роутерами

### Структура роутера

```python
# api/routers/products.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.dependencies import get_model
from sql_model.model import SQLAlchemyModel
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["products"])

# Pydantic модели (для валидации и документации)
class ProductCreate(BaseModel):
    name: str
    price: float

class ProductUpdate(BaseModel):
    name: str
    price: float

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    
    class Config:
        from_attributes = True

# GET - получить все
@router.get("/", response_model=list[ProductResponse])
def list_products(model: SQLAlchemyModel = Depends(get_model)):
    """Получить список всех продуктов."""
    products = model.products().get_all()
    return products

# GET - получить по ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, model: SQLAlchemyModel = Depends(get_model)):
    """Получить продукт по ID."""
    product = model.products().get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# POST - создать
@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, model: SQLAlchemyModel = Depends(get_model)):
    """Создать новый продукт."""
    try:
        product = model.products().create(data.name, data.price)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# PUT - обновить
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    model: SQLAlchemyModel = Depends(get_model)
):
    """Обновить продукт."""
    try:
        product = model.products().update(product_id, data.name, data.price)
        return product
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# DELETE - удалить
@router.delete("/{product_name}")
def delete_product(product_name: str, model: SQLAlchemyModel = Depends(get_model)):
    """Удалить продукт по названию."""
    try:
        model.products().delete(product_name)
        return {"message": f"Product '{product_name}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Подключение роутеров в main.py

```python
# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers import products, stock, sales, suppliers, orders, expenses

app = FastAPI(title="Bakery Management API")

# Подключить роутеры
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(sales.router)
app.include_router(suppliers.router)
app.include_router(orders.router)
app.include_router(expenses.router)

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")
```

---

## Частые сценарии

### Сценарий 1: Учет покупки сырья

```python
# Клиент купил 100 kg муки у поставщика "ООО Мука"
# 1. Создать поставщика (если его нет)
supplier = model.suppliers().get_by_name("ООО Мука")
if not supplier:
    supplier = model.suppliers().create("ООО Мука", "+7-999-123-45-67")

# 2. Создать запас (если его нет)
stock = model.stock().get_by_name("Мука пшеничная")
if not stock:
    stock = model.stock().create("Мука пшеничная", "Materials", 0, "kg")

# 3. Создать тип расхода (если его нет)
exp_type = model.expense_types().get_by_name("Мука пшеничная")
if not exp_type:
    exp_type = model.expense_types().create(
        "Мука пшеничная",
        20.0,  # цена за kg
        category="Raw Materials",
        stock=True  # это товар из stock
    )

# 4. Создать документ расхода (счет)
doc = model.expense_documents().create(
    date="2024-01-15",
    supplier_id=supplier.id,
    total_amount=2000.0,  # 100 kg × 20
    comment="Закупка муки"
)

# 5. Добавить позицию в документ
item = model.expense_documents().add_item(
    document_id=doc.id,
    expense_type_id=exp_type.id,
    stock_item_id=stock.id,
    quantity=100.0,
    price_per_unit=20.0
)

# 6. Увеличить количество на складе
model.stock().update_quantity(stock.id, stock.quantity + 100.0)

print(f"✓ Закупка записана. На складе теперь: {stock.quantity + 100} kg")
```

### Сценарий 2: Запись продажи с учетом использования сырья

```python
# Продали 5 батонов по 250 с скидкой 10%
# 1. Записать продажу
sale = model.sales().create(
    product_id=1,
    product_name="Батон",
    price=250,
    quantity=5,
    discount=10,
    date="2024-01-15"
)

# 2. Уменьшить количество ингредиентов на складе
# (эта логика должна быть в recipes/ingredients)
flour_used = 0.5 * 5  # 0.5 kg муки на один батон
model.stock().update_quantity("Мука", model.stock().get_by_name("Мука").quantity - flour_used)

# 3. Посчитать доход
income = model.calculate_income()
print(f"✓ Продажа записана. Доход: {income}")
```

### Сценарий 3: Отчет о прибыли

```python
# Получить финансовый отчет
income = model.calculate_income()
expenses = model.calculate_expenses()
profit = model.calculate_profit()

print(f"Доход: {income}")
print(f"Расходы: {expenses}")
print(f"Прибыль: {profit}")

# Получить детальную информацию
sales_list = model.sales().get_all()
print(f"\nПродажи ({len(sales_list)} позиций):")
for sale in sales_list:
    amount = sale.price * sale.quantity * (1 - sale.discount / 100)
    print(f"  - {sale.product_name}: {amount}")

expense_docs = model.expense_documents().get_all()
print(f"\nРасходы ({len(expense_docs)} документов):")
for doc in expense_docs:
    print(f"  - {doc.supplier.name}: {doc.total_amount}")
```

### Сценарий 4: Проверка целостности данных

```python
# Проверить, нет ли «висящих» ссылок
def validate_database(model):
    errors = []
    
    # Проверить продажи на существующие продукты
    sales = model.sales().get_all()
    for sale in sales:
        if not model.products().get_by_id(sale.product_id):
            errors.append(f"Sale {sale.id}: product {sale.product_id} not found")
    
    # Проверить списания
    writeoffs = model.writeoffs().get_all()
    for wo in writeoffs:
        if wo.product_id and not model.products().get_by_id(wo.product_id):
            errors.append(f"WriteOff {wo.id}: product {wo.product_id} not found")
        if wo.stock_item_id and not model.stock().get_by_id(wo.stock_item_id):
            errors.append(f"WriteOff {wo.id}: stock item {wo.stock_item_id} not found")
    
    if errors:
        print("Найдены ошибки:")
        for error in errors:
            print(f"  ⚠️  {error}")
    else:
        print("✓ База данных в порядке")
    
    return len(errors) == 0

validate_database(model)
```

---

## Отладка и логирование

### Включить SQL логирование

```python
# sql_model/database.py
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True  # Выведет все SQL запросы!
)
```

### Логирование в файл

```python
import logging

logging.basicConfig(
    filename='bakery.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# В репозиториях:
logger.info(f"Created product: {product.name}")
logger.error(f"Failed to delete product: {error}")
```

### Дебагинг с pdb

```python
# Добавить breakpoint в нужное место
def some_function():
    data = model.products().get_all()
    breakpoint()  # Приостановит выполнение
    # Теперь можешь исследовать переменные
```

### Вывод SQL запроса

```python
from sqlalchemy import text

# Выполнить custom SQL запрос
result = model.db.execute(text("SELECT COUNT(*) FROM products"))
print(result.scalar())

# Или через ORM:
from sqlalchemy import func
count = model.db.query(func.count(Product.id)).scalar()
print(count)
```

---

## Тестирование

### Пример теста для репозитория

```python
# tests/test_products.py
import pytest
from sql_model.model import SQLAlchemyModel

@pytest.fixture
def model():
    """Создать временную БД для тестов."""
    from sql_model.database import SessionLocal, init_db
    from sql_model.entities import Base, Product
    
    # Инициализировать временную БД
    init_db()
    yield model
    # Cleanup
    model.close()

def test_create_product(model):
    """Тест создания продукта."""
    product = model.products().create("Test Product", 100)
    assert product.id is not None
    assert product.name == "Test Product"
    assert product.price == 100

def test_get_product(model):
    """Тест получения продукта."""
    created = model.products().create("Test Product", 100)
    found = model.products().get_by_id(created.id)
    assert found is not None
    assert found.name == "Test Product"

def test_update_product(model):
    """Тест обновления продукта."""
    created = model.products().create("Test Product", 100)
    updated = model.products().update(created.id, "Updated", 150)
    assert updated.name == "Updated"
    assert updated.price == 150

def test_delete_product(model):
    """Тест удаления продукта."""
    created = model.products().create("Test Product", 100)
    deleted = model.products().delete("Test Product")
    assert deleted is True
    assert model.products().get_by_id(created.id) is None
```

---

**Последнее обновление:** 2024-01-18  
**Версия:** 1.0
