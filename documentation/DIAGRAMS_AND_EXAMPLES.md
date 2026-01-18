# 📊 Диаграммы и визуальные примеры

## 1. Диаграмма потока данных

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Web Application                     │
│                        (main.py)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
      ┌────────────────────────────────┐
      │      API Routers                │
      │   (api/routers/*.py)            │
      │                                 │
      │  /products /stock /sales        │
      │  /suppliers /orders /expenses   │
      └──────────┬───────────────────┘
                 │
                 ↓
      ┌────────────────────────────────┐
      │    Repositories                 │
      │  (repositories/*.py)            │
      │                                 │
      │  ProductsRepository             │
      │  StockRepository                │
      │  SalesRepository                │
      │  SupplierRepository             │
      └──────────┬───────────────────┘
                 │
                 ↓
      ┌────────────────────────────────┐
      │  SQLAlchemy ORM                 │
      │  (sql_model/entities.py)        │
      │                                 │
      │  Product, StockItem, Sale       │
      │  Supplier, Order, etc.          │
      └──────────┬───────────────────┘
                 │
                 ↓
      ┌────────────────────────────────┐
      │    SQLite Database              │
      │  (bakery_management.db)         │
      │                                 │
      │  ╔═══════════════════════════╗ │
      │  ║ products                  ║ │
      │  ╟─────────────────────────╢ │
      │  ║ id | name | price       ║ │
      │  ╚═══════════════════════════╝ │
      │                                 │
      │  ╔═══════════════════════════╗ │
      │  ║ stock                     ║ │
      │  ╟─────────────────────────╢ │
      │  ║ id | name | qty | unit ║ │
      │  ╚═══════════════════════════╝ │
      │                                 │
      │  + 11 других таблиц...         │
      └────────────────────────────────┘
```

---

## 2. Как добавляется продукт (пример на диаграмме)

### Пример: Добавить новый батон

```
1. FRONTEND (HTML форма)
   ┌──────────────────────┐
   │ Название: "Батон"   │
   │ Цена: 250            │
   │ [Сохранить]          │
   └──────────────────────┘
                │
                │ POST /products
                │ Content-Type: application/json
                │ {"name": "Батон", "price": 250}
                ↓
2. BACKEND API (api/routers/products.py)
   @router.post("/")
   def create_product(data: ProductCreate):
       return model.products().create(data.name, data.price)
                │
                │
                ↓
3. REPOSITORY (repositories/products.py)
   def create(self, name: str, price: float) -> Product:
       product = Product(name=name, price=price)
       self.db.add(product)
       self.db.commit()
       return product
                │
                │
                ↓
4. ORM (sql_model/entities.py)
   class Product(Base):
       __tablename__ = "products"
       id: int
       name: str (UNIQUE)
       price: float
                │
                │ SQL: INSERT INTO products (name, price) 
                │      VALUES ('Батон', 250)
                ↓
5. DATABASE (bakery_management.db)
   ┌──────────────────────────┐
   │ products                 │
   ├──────────────────────────┤
   │ id │ name    │ price    │
   ├────┼─────────┼──────────┤
   │ 1  │ Батон  │ 250      │ ← НОВАЯ ЗАПИСЬ
   └──────────────────────────┘
```

---

## 3. Структура Product с отношениями

```
                    ┌─────────────┐
                    │   Product   │
                    ├─────────────┤
                    │ id (PK)     │
                    │ name        │
                    │ price       │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          │ 1:N            │ 1:N            │ 1:N
          ↓                ↓                ↓
    ┌──────────┐      ┌─────────┐    ┌──────────────┐
    │  Sales   │      │ WriteOff│    │  OrderItems  │
    ├──────────┤      ├─────────┤    ├──────────────┤
    │ id (PK)  │      │ id (PK) │    │ id (PK)      │
    │ prod_id  │      │ prod_id │    │ order_id     │
    │ quantity │      │ quantity│    │ product_id   │
    │ price    │      │ reason  │    │ quantity     │
    │ discount │      │ date    │    │ price        │
    │ date     │      └─────────┘    └──────────────┘
    └──────────┘
```

---

## 4. Сложный пример: Закупка и продажа

### Сценарий: Купить 100kg муки, сделать батоны, продать

```
ДЕНЬ 1: ЗАКУПКА СЫРЬЯ
═══════════════════════

1. Создается Supplier
   ┌──────────────────────┐
   │ Supplier: "ООО Мука" │
   │ Phone: +7-999-123-45 │
   └──────────────────────┘

2. Создается StockItem
   ┌────────────────────────────┐
   │ Stock: "Мука пшеничная"    │
   │ Category: Materials        │
   │ Quantity: 0 kg (пока)      │
   │ Unit: kg                   │
   └────────────────────────────┘

3. Создается ExpenseType
   ┌──────────────────────────────┐
   │ Type: "Мука пшеничная"       │
   │ Default Price: 20.0 за kg   │
   │ Category: Raw Materials      │
   │ Stock: true (это товар!)     │
   └──────────────────────────────┘

4. Создается ExpenseDocument (счет от поставщика)
   ┌─────────────────────────────────┐
   │ Document ID: 1                  │
   │ Date: 2024-01-15                │
   │ Supplier: "ООО Мука"            │
   │ Total: 2000.0                   │
   └─────────────────────────────────┘

5. Добавляются ExpenseItems (строки в счете)
   ┌──────────────────────────────────────┐
   │ Item 1:                              │
   │   Type: Мука пшеничная              │
   │   Quantity: 100 kg                   │
   │   Price per unit: 20.0               │
   │   Total: 2000.0                      │
   │   Stock item: "Мука пшеничная" ──┐  │
   │                                   │  │
   └───────────────────────────────────┼──┘
                                       │
6. UPDATE STOCK (увеличить количество)
   ┌────────────────────────────────┐
   │ Stock: "Мука пшеничная"        │
   │ Quantity: 0 + 100 = 100 kg     │ ← ОБНОВЛЕНО
   └────────────────────────────────┘


ДЕНЬ 2: ПРОИЗВОДСТВО И ПРОДАЖА
═══════════════════════════════

1. Создается Product
   ┌────────────────────┐
   │ Product: "Батон"  │
   │ Price: 250         │
   └────────────────────┘

2. Производство батонов (логика приложения)
   Один батон = 0.5 kg муки + другие ингредиенты
   
   Производим 200 батонов:
   - Нужно: 200 × 0.5 = 100 kg муки
   
3. UPDATE STOCK (уменьшить количество муки)
   ┌────────────────────────────────┐
   │ Stock: "Мука пшеничная"        │
   │ Quantity: 100 - 100 = 0 kg     │ ← ОБНОВЛЕНО
   └────────────────────────────────┘

4. Создаются Sales (продажи)
   ┌─────────────────────────────────────┐
   │ Sale 1:                             │
   │   Product: 1 (Батон)               │
   │   Quantity: 50                      │
   │   Price: 250                        │
   │   Discount: 0%                      │
   │   Income: 50 × 250 = 12500          │
   │                                     │
   │ Sale 2:                             │
   │   Product: 1 (Батон)               │
   │   Quantity: 100                     │
   │   Price: 250                        │
   │   Discount: 10%                     │
   │   Income: 100 × 250 × 0.9 = 22500   │
   │                                     │
   │ Sale 3:                             │
   │   Product: 1 (Батон)               │
   │   Quantity: 50                      │
   │   Price: 250                        │
   │   Discount: 0%                      │
   │   Income: 50 × 250 = 12500          │
   └─────────────────────────────────────┘
   Total Sales: 50 + 100 + 50 = 200 батонов


ДЕНЬ 3: ОТЧЕТ
══════════════

Расчет доходов:
Income = SUM(price × quantity × (1 - discount/100))
       = 12500 + 22500 + 12500
       = 47500

Расчет расходов:
Expenses = SUM(total_amount) из ExpenseDocuments
         = 2000

Прибыль:
Profit = Income - Expenses
       = 47500 - 2000
       = 45500
```

---

## 5. Диаграмма связей все таблицы

```
                    ┌─────────┐
                    │  UNITS  │
                    └────┬────┘
         ┌──────────────┼──────────────┬──────────────┐
         │              │              │              │
    STOCK_ITEM       WRITEOFF      EXPENSE_ITEM       │
         │              │              │              │
         │              │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼─────┐      │
    │  STOCK   │    │ WRITEOFF │    │ EXPENSE  │    │
    │ CATEGORY │    │          │    │  ITEM    │    │
    │          │    │ Product? │    │          │    │
    │ Materials│    │ Stock?   │    │ Type     │────┼─→ EXPENSE_TYPE
    │ Packaging│    └──────────┘    │ Stock?   │    │
    └──────────┘                    │ Quantity │    │
                                    │ Price    │    │
                    ┌─────────┐     └──────────┘    │
                    │ PRODUCTS│                     │
                    │         │     ┌──────────┐    │
                    │ Sales?  │     │ EXPENSE  │    │
                    │ Orders? │─────│ DOCUMENT │◄───┘
                    │ Writeoff?     │          │
                    └─────────┘     │ Supplier │
                                    │ Date     │
                    ┌──────────┐    │ Total    │
                    │  SALES   │    └──────────┘
                    │          │         │
                    │ Product  │         │ 1:N
                    │ Quantity │         │
                    │ Price    │    ┌────▼──────┐
                    │ Discount │    │ SUPPLIER  │
                    │ Date     │    │           │
                    └──────────┘    │ Name      │
                                    │ Phone     │
                    ┌──────────┐    │ Email     │
                    │  ORDERS  │    └───────────┘
                    │          │
                    │ Status   │
                    │ Created  │
                    │ Complete │
                    └────┬─────┘
                         │ 1:N
                    ┌────▼───────────┐
                    │  ORDER_ITEMS   │
                    │                │
                    │ Product        │
                    │ Quantity       │
                    │ Price          │
                    └────────────────┘
```

---

## 6. Процесс расширения системы (step by step)

### Хочу добавить "Категории продуктов"

```
ЭТАП 1: Создать сущность
════════════════════════

В sql_model/entities.py:
┌──────────────────────────────────────────┐
│ class ProductCategory(Base):             │
│     __tablename__ = "product_categories" │
│                                          │
│     id: Mapped[int]                      │
│     name: Mapped[str]                    │
│     description: Mapped[Optional[str]]   │
│                                          │
│     # Relationships                      │
│     products: Mapped[List["Product"]]    │
└──────────────────────────────────────────┘


ЭТАП 2: Обновить Product
═════════════════════════

В sql_model/entities.py:
┌──────────────────────────────────────────┐
│ class Product(Base):                     │
│     ...                                  │
│     category_id: Mapped[int] = FK        │
│                                          │
│     category: Mapped["ProductCategory"]  │
└──────────────────────────────────────────┘


ЭТАП 3: Создать репозиторий
════════════════════════════

repositories/product_categories.py:
┌───────────────────────────────────────┐
│ class ProductCategoriesRepository:    │
│     def __init__(self, db: Session)   │
│     def create(...)                   │
│     def get_all()                     │
│     def get_by_id()                   │
│     def update()                      │
│     def delete()                      │
└───────────────────────────────────────┘


ЭТАП 4: Добавить в Model
═════════════════════════

В sql_model/model.py:
┌────────────────────────────────────┐
│ from repositories.product_categor… │
│                                    │
│ class SQLAlchemyModel:             │
│     def __init__(self):            │
│         self._categories_repo = …  │
│                                    │
│     def product_categories(self):  │
│         return self._categories_… │
└────────────────────────────────────┘


ЭТАП 5: Создать API роутер
═══════════════════════════

api/routers/product_categories.py:
┌────────────────────────────────────┐
│ @router.get("/")                   │
│ @router.post("/", status_code=201) │
│ @router.put("/{id}")               │
│ @router.delete("/{id}")            │
│                                    │
│ Каждый метод использует model…     │
└────────────────────────────────────┘


ЭТАП 6: Подключить в main.py
═════════════════════════════

В main.py:
┌──────────────────────────────────────┐
│ from api.routers import              │
│     product_categories               │
│                                      │
│ app.include_router(                  │
│     product_categories.router        │
│ )                                    │
└──────────────────────────────────────┘


ЭТАП 7: Пересоздать БД и ТЕСТИРОВАТЬ
═════════════════════════════════════

bash:
$ rm bakery_management.db
$ python main.py  # Создаст новую БД

API тест:
POST /product_categories
{"name": "Хлеб", "description": "Хлебные изделия"}


РЕЗУЛЬТАТ:
══════════

Теперь:
✓ Можно создавать категории
✓ Можно связывать батоны с категорией
✓ API доступен по /product_categories
✓ БД содержит таблицу product_categories
✓ Бизнес-логика в репозитории
```

---

## 7. SQL примеры (если нужно писать сложные запросы)

```python
from sqlalchemy import func, text
from sql_model.entities import Sale, Product, ExpenseDocument

# 1. Топ 5 самых проданных продуктов
top_products = model.db.query(
    Sale.product_name,
    func.sum(Sale.quantity).label('total_qty')
).group_by(
    Sale.product_name
).order_by(
    func.sum(Sale.quantity).desc()
).limit(5).all()

# 2. Доход по дням за месяц
daily_income = model.db.query(
    Sale.date,
    func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, float) / 100))
).group_by(
    Sale.date
).all()

# 3. Средняя цена продуктов
avg_price = model.db.query(
    func.avg(Product.price)
).scalar()

# 4. Расходы по категориям
expenses_by_category = model.db.query(
    func.sum(ExpenseDocument.total_amount)
).group_by(
    ExpenseDocument.supplier_id
).all()
```

---

## 8. Обработка ошибок (примеры)

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

try:
    # Попытка создать продукт с дублирующимся именем
    model.products().create("Батон", 250)
    model.products().create("Батон", 300)  # ← ОШИБКА!
    
except IntegrityError:
    # Уникальное ограничение нарушено
    print("✗ Продукт с таким именем уже существует")
    
except SQLAlchemyError as e:
    # Другая ошибка БД
    print(f"✗ Ошибка БД: {e}")
    
except ValueError as e:
    # Ошибка валидации
    print(f"✗ Ошибка валидации: {e}")
    
except Exception as e:
    # Неожиданная ошибка
    print(f"✗ Неожиданная ошибка: {e}")
    raise
```

---

**Дополнительно смотри:**
- [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) - Полная архитектура
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Примеры кода
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Быстрая справка
