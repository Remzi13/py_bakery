# 📋 Архитектура базы данных - Bakery Management System

## Оглавление
1. [Обзор системы](#обзор-системы)
2. [Структура базы данных](#структура-базы-данных)
3. [Схема и связи таблиц](#схема-и-связи-таблиц)
4. [Описание сущностей](#описание-сущностей)
5. [Как работает система](#как-работает-система)
6. [Вносим изменения и расширяем](#вносим-изменения-и-расширяем)
7. [Примеры запросов](#примеры-запросов)

---

## Обзор системы

**Bakery Management System** - это система управления пекарней на Python с использованием:
- **SQLAlchemy ORM** - для работы с БД
- **SQLite** - как СУБД
- **FastAPI** - как веб-фреймворк
- **Repository Pattern** - для доступа к данным

### Основной файл конфигурации БД
```
sql_model/
├── database.py      # Подключение к БД, инициализация
├── entities.py      # Все модели (таблицы)
└── model.py         # Класс SQLAlchemyModel - фасад для работы с БД
```

---

## Структура базы данных

### Файл базы данных
```
./bakery_management.db  # SQLite база данных (автоматически создается)
```

### Инициализация БД
```python
# sql_model/database.py
DATABASE_URL = "sqlite:///./bakery_management.db"
# Foreign keys включены через PRAGMA
```

---

## Схема и связи таблиц

### ER-диаграмма (текстовое представление)

```
┌─────────────────┐
│     UNITS       │ (единицы измерения)
├─────────────────┤
│ id (PK)         │
│ name (UNIQUE)   │
└────────┬────────┘
         │ 1:N
         ├──────────────────────┬──────────────────┬──────────────┐
         │                      │                  │              │
    ┌────▼─────────┐   ┌───────▼──────┐  ┌────────▼────┐  ┌──────▼──────┐
    │  STOCK       │   │  WRITEOFFS   │  │  EXPENSES   │  │  ORDERS     │
    │  (inventory) │   │  (write-offs)│  │  (expenses) │  │  (orders)   │
    └──────────────┘   └──────────────┘  └─────────────┘  └─────────────┘
         │ N:1              │ N:1              │ N:1              │ 1:N
         │                  │                  │                  │
    ┌────▼──────────┐   ┌───▼────────┐  ┌────▼──────────┐  ┌─────▼───────┐
    │ STOCK_        │   │ PRODUCTS   │  │ EXPENSE_      │  │ ORDER_ITEMS │
    │ CATEGORIES    │   │            │  │ TYPES         │  │             │
    └───────────────┘   └────────────┘  └────┬──────────┘  └─────────────┘
                             │ 1:N           │ N:1
                             │               │
                        ┌────▼──┐      ┌─────▼────────────┐
                        │ SALES │      │ EXPENSE_         │
                        │       │      │ CATEGORIES       │
                        └───────┘      └──────────────────┘

┌──────────────────┐
│   SUPPLIERS      │
├──────────────────┤
│ id (PK)          │
│ name (UNIQUE)    │
│ contact_person   │
│ phone            │
│ email            │
│ address          │
└────────┬─────────┘
         │ 1:N
         │
    ┌────▼──────────────┐
    │ EXPENSE_          │
    │ DOCUMENTS         │
    │ (documents/       │
    │  invoices)        │
    └────────┬──────────┘
             │ 1:N
             │
        ┌────▼──────────────┐
        │ EXPENSE_ITEMS     │
        │ (line items)      │
        └───────────────────┘
```

---

## Описание сущностей

### 📌 1. UNITS (Единицы измерения)
**Таблица:** `units`
**Назначение:** Хранит единицы измерения (kg, g, l, piece и т.д.)

```python
class Unit(Base):
    id: int (PK)
    name: str (UNIQUE)
```

**Примеры:** 
- kg (килограмм)
- l (литр)
- g (грамм)
- piece (штука)

**Связи:**
- 1:N → StockItem
- 1:N → WriteOff
- 1:N → ExpenseItem

---

### 📌 2. STOCK_CATEGORIES (Категории запасов)
**Таблица:** `stock_categories`
**Назначение:** Классификация запасов/сырья

```python
class StockCategory(Base):
    id: int (PK)
    name: str (UNIQUE)
```

**Примеры:**
- Materials (сырье: мука, сахар)
- Packaging (упаковка)
- Equipment (оборудование)

**Связи:**
- 1:N → StockItem

---

### 📌 3. STOCK (Запасы/Инвентарь)
**Таблица:** `stock`
**Назначение:** Учет материалов, сырья и запасов

```python
class StockItem(Base):
    id: int (PK)
    name: str (UNIQUE)
    category_id: int (FK → stock_categories)
    quantity: float (текущее количество)
    unit_id: int (FK → units)
```

**Примеры:** 
- Мука (50 kg)
- Масло (10 l)
- Дрожжи (500 g)

**Связи:**
- N:1 → Unit
- N:1 → StockCategory
- 1:N → WriteOff
- 1:N → ExpenseItem

---

### 📌 4. PRODUCTS (Готовые продукты)
**Таблица:** `products`
**Назначение:** Готовые товары для продажи

```python
class Product(Base):
    id: int (PK)
    name: str (UNIQUE)
    price: float (цена продажи)
```

**Примеры:**
- Белый хлеб (200 price units)
- Батон (300 price units)
- Булка (150 price units)

**Связи:**
- 1:N → Sale
- 1:N → WriteOff
- 1:N → OrderItem

---

### 📌 5. SALES (Продажи)
**Таблица:** `sales`
**Назначение:** Учет всех продаж продуктов

```python
class Sale(Base):
    id: int (PK)
    product_id: int (FK → products)
    product_name: str (копия имени продукта)
    price: float (цена в момент продажи)
    quantity: float (количество проданного)
    discount: int (скидка в процентах)
    date: str (дата продажи YYYY-MM-DD)
```

**Связи:**
- N:1 → Product

**Бизнес-логика:**
```
Доход от продажи = цена × количество × (1 - скидка/100)
```

---

### 📌 6. EXPENSE_CATEGORIES (Категории расходов)
**Таблица:** `expense_categories`
**Назначение:** Классификация финансовых расходов

```python
class ExpenseCategory(Base):
    id: int (PK)
    name: str (UNIQUE)
```

**Примеры:**
- Raw Materials (закупка сырья)
- Utilities (коммунальные услуги)
- Rent (аренда помещения)
- Salaries (зарплаты)
- Transport (доставка)

**Связи:**
- 1:N → ExpenseType

---

### 📌 7. EXPENSE_TYPES (Типы расходов)
**Таблица:** `expense_types`
**Назначение:** Конкретные типы расходов (более детальные)

```python
class ExpenseType(Base):
    id: int (PK)
    name: str (UNIQUE)
    default_price: float (стандартная цена)
    category_id: int (FK → expense_categories)
    stock: bool (это товар из stock или нет?)
```

**Примеры:**
- Flour (Мука - category: Raw Materials, stock: true)
- Rent Payment (Оплата аренды - category: Rent, stock: false)
- Electricity (Электричество - category: Utilities, stock: false)

**Связи:**
- N:1 → ExpenseCategory
- 1:N → ExpenseItem

**Особенность:** 
- Если `stock=true`, при добавлении расхода можно связать с `StockItem`
- Если `stock=false`, это просто финансовый расход

---

### 📌 8. SUPPLIERS (Поставщики)
**Таблица:** `suppliers`
**Назначение:** Данные поставщиков сырья и услуг

```python
class Supplier(Base):
    id: int (PK)
    name: str (UNIQUE)
    contact_person: str (optional - ФИО контактного лица)
    phone: str (optional - телефон)
    email: str (optional - email)
    address: str (optional - адрес)
```

**Примеры:**
- ООО "Мука и Зерно" (поставщик сырья)
- ООО "Упакофф" (поставщик упаковки)
- ИП Петров (электричество)

**Связи:**
- 1:N → ExpenseDocument

---

### 📌 9. EXPENSE_DOCUMENTS (Документы о расходах)
**Таблица:** `expense_documents`
**Назначение:** Счета/накладные от поставщиков

```python
class ExpenseDocument(Base):
    id: int (PK)
    date: str (дата документа YYYY-MM-DD)
    supplier_id: int (FK → suppliers)
    total_amount: float (общая сумма по документу)
    comment: str (optional - примечание)
```

**Примеры:** 
- Счет-фактура от поставщика мучных изделий
- Накладная на электричество
- Квитанция об оплате аренды

**Связи:**
- N:1 → Supplier
- 1:N → ExpenseItem (каждый документ может содержать несколько строк)

---

### 📌 10. EXPENSE_ITEMS (Строки расходов)
**Таблица:** `expense_items`
**Назначение:** Позиции в документах о расходах

```python
class ExpenseItem(Base):
    id: int (PK)
    document_id: int (FK → expense_documents) [CASCADE DELETE]
    expense_type_id: int (FK → expense_types)
    stock_item_id: int (FK → stock, optional)
    unit_id: int (FK → units)
    quantity: float (количество)
    price: float (цена )    
```

**Пример:**
```
Document: Счет от "Мука и Зерно" на сумму 1000
  └─ Item 1: Мука (пшеничная) - 50 kg × 15 = 750
  └─ Item 2: Сахар - 10 kg × 25 = 250
```

**Связи:**
- N:1 → ExpenseDocument (при удалении документа, удаляются и его item'ы)
- N:1 → ExpenseType
- N:1 → StockItem (если это товар из stock)
- N:1 → Unit

**Бизнес-логика:**
- Если `stock_item_id` не null, количество может увеличивать stock
- Если `stock_item_id` null, это просто финансовый расход

---

### 📌 11. WRITEOFFS (Списания)
**Таблица:** `writeoffs`
**Назначение:** Учет списаний товаров и материалов (брак, порча)

```python
class WriteOff(Base):
    id: int (PK)
    product_id: int (FK → products, optional)
    stock_item_id: int (FK → stock, optional)
    unit_id: int (FK → units, optional)
    quantity: float (количество списано)
    reason: str (причина: брак, порча, истечение срока)
    date: str (дата списания YYYY-MM-DD)
```

**Примеры:**
- Списание 5 батонов (брак)
- Списание 2 kg муки (подмокла, порчена)
- Списание 10 хлебов (истечение срока)

**Связи:**
- N:1 → Product (если списывается готовый товар)
- N:1 → StockItem (если списывается сырье)
- N:1 → Unit

**Логика:**
- Либо `product_id` не null, либо `stock_item_id` не null
- Это важно для отчетности и анализа потерь

---

### 📌 12. ORDERS (Заказы)
**Таблица:** `orders`
**Назначение:** Заказы с отложенным выполнением

```python
class Order(Base):
    id: int (PK)
    created_date: str (дата создания заказа YYYY-MM-DD)
    status: str (pending / completed)
    completion_date: str (optional - дата выполнения)
    additional_info: str (optional - примечание)
```

**Примеры:**
- Заказ на 50 хлебов к пятнице
- Заказ на торт на свадьбу

**Связи:**
- 1:N → OrderItem

---

### 📌 13. ORDER_ITEMS (Позиции в заказе)
**Таблица:** `order_items`
**Назначение:** Товары в составе заказа

```python
class OrderItem(Base):
    id: int (PK)
    order_id: int (FK → orders) [CASCADE DELETE]
    product_id: int (FK → products)
    product_name: str (копия имени продукта)
    quantity: float (количество)
    price: float (цена за единицу)
```

**Пример:**
```
Order #1: Заказ на свадьбу (статус: pending)
  └─ Item 1: Свадебный торт - 1 × 5000
  └─ Item 2: Батон белый - 20 × 200
  └─ Item 3: Булки сдобные - 50 × 150
```

**Связи:**
- N:1 → Order (при удалении заказа, удаляются все его items)
- N:1 → Product

---

## Как работает система

### 1. Инициализация БД

```python
# sql_model/database.py
from sql_model.database import init_db

# При первом запуске:
init_db()  # Создает таблицы и заполняет справочные данные
```

Функция `init_db()` автоматически:
- Создает все таблицы
- Добавляет базовые единицы измерения (kg, g, l, piece)
- Добавляет базовые категории

### 2. Работа с моделью (Facade Pattern)

```python
from sql_model.model import SQLAlchemyModel

# Создаем модель - единая точка доступа к БД
model = SQLAlchemyModel()

# Доступ к репозиториям через методы
model.products()        # ProductsRepository
model.stock()           # StockRepository
model.sales()           # SalesRepository
model.suppliers()       # SuppliersRepository
model.expense_types()   # ExpenseTypesRepository
model.expense_documents()  # ExpenseDocumentsRepository
model.orders()          # OrdersRepository
model.writeoffs()       # WriteOffsRepository
```

### 3. Примеры операций

**Добавить новый продукт:**
```python
model.products().create("Батон", 250)
```

**Добавить запас:**
```python
model.stock().create(
    "Мука пшеничная",
    category="Materials",
    quantity=50.0,
    unit="kg"
)
```

**Записать продажу:**
```python
model.sales().create(
    product_id=1,
    quantity=5,
    price=250,
    discount=0,
    date="2024-01-15"
)
```

**Добавить расход:**
```python
doc = model.expense_documents().create(
    date="2024-01-15",
    supplier_id=1,
    total_amount=1000.0
)

model.expense_documents().add_item(
    document_id=doc.id,
    expense_type_id=1,
    stock_item_id=1,
    quantity=50,
    price=20
)
```

### 4. Расчеты

```python
# Общий доход
income = model.calculate_income()

# Общие расходы
expenses = model.calculate_expenses()

# Прибыль
profit = model.calculate_profit()
```

---

## Вносим изменения и расширяем

### Сценарий 1: Добавить новое поле к существующей таблице

**Задача:** Добавить поле `description` к таблице Products

**Шаги:**

1. **Отредактируй сущность** (`sql_model/entities.py`):
```python
class Product(Base):
    """Готовый продукт для продажи."""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # НОВОЕ
    
    # ... остальное
```

2. **Обнови репозиторий** (`repositories/products.py`):
```python
def create(self, name: str, price: float, description: str = None) -> Product:
    product = Product(
        name=name,
        price=price,
        description=description
    )
    self.db.add(product)
    self.db.commit()
    return product
```

3. **Пересоздай БД:**
```bash
# Удали старую БД (или используй миграции)
del bakery_management.db

# При следующем запуске будет создана новая с новым полем
```

**⚠️ Важно:** SQLAlchemy создает таблицы только для новых проектов. Для более сложных изменений используй Alembic (миграции).

---

### Сценарий 2: Добавить новую сущность (таблицу)

**Задача:** Добавить таблицу для отзывов клиентов

**Шаги:**

1. **Создай сущность** в `sql_model/entities.py`:
```python
class CustomerReview(Base):
    """Отзыв клиента о продукте."""
    __tablename__ = "customer_reviews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    
    def __repr__(self):
        return f"<CustomerReview(id={self.id}, product_id={self.product_id}, rating={self.rating})>"
```

2. **Обнови Product** в `sql_model/entities.py`:
```python
class Product(Base):
    # ... существующие поля
    
    # Relationships
    sales: Mapped[List["Sale"]] = relationship("Sale", back_populates="product")
    write_offs: Mapped[List["WriteOff"]] = relationship("WriteOff", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")
    reviews: Mapped[List["CustomerReview"]] = relationship("CustomerReview", back_populates="product")  # НОВОЕ
```

3. **Создай репозиторий** `repositories/customer_reviews.py`:
```python
from sqlalchemy.orm import Session
from sql_model.entities import CustomerReview

class CustomerReviewsRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, product_id: int, rating: int, comment: str, date: str) -> CustomerReview:
        review = CustomerReview(
            product_id=product_id,
            rating=rating,
            comment=comment,
            date=date
        )
        self.db.add(review)
        self.db.commit()
        return review
    
    def get_by_product(self, product_id: int) -> list[CustomerReview]:
        return self.db.query(CustomerReview).filter_by(product_id=product_id).all()
```

4. **Добавь в модель** `sql_model/model.py`:
```python
from repositories.customer_reviews import CustomerReviewsRepository

class SQLAlchemyModel:
    def __init__(self):
        # ... существующие репозитории
        self._reviews_repo = CustomerReviewsRepository(self.db)
    
    def customer_reviews(self) -> CustomerReviewsRepository:
        return self._reviews_repo
```

5. **Пересоздай БД** (удали старую, будет создана новая со всеми таблицами)

---

### Сценарий 3: Добавить новый метод расчета

**Задача:** Добавить расчет среднего рейтинга продукта

**Шаги:**

1. **Добавь метод в репозиторий** (`repositories/customer_reviews.py`):
```python
from sqlalchemy import func

def get_average_rating(self, product_id: int) -> float:
    result = self.db.query(func.avg(CustomerReview.rating)).filter_by(product_id=product_id).scalar()
    return float(result) if result is not None else 0.0
```

2. **Используй в модели или API:**
```python
avg_rating = model.customer_reviews().get_average_rating(product_id=1)
```

---

### Сценарий 4: Добавить constrain (ограничение)

**Задача:** Гарантировать, что количество на складе не может быть отрицательным

**Шаги:**

1. **Обнови сущность** в `sql_model/entities.py`:
```python
from sqlalchemy import CheckConstraint

class StockItem(Base):
    """Инвентарь/Запас."""
    __tablename__ = "stock"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('stock_categories.id'), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_quantity_positive'),
    )
```

2. **Добавь проверку в репозиторий:**
```python
def update(self, stock_id: int, quantity: float):
    if quantity < 0:
        raise ValueError("Количество не может быть отрицательным")
    
    stock = self.db.query(StockItem).filter_by(id=stock_id).first()
    if stock:
        stock.quantity = quantity
        self.db.commit()
```

---

### Сценарий 5: Добавить индекс для производительности

**Задача:** Ускорить поиск продаж по дате

**Шаги:**

1. **Обнови сущность** в `sql_model/entities.py`:
```python
from sqlalchemy import Index

class Sale(Base):
    """Проданный продукт."""
    __tablename__ = "sales"
    
    # ... существующие поля
    
    # Indexes
    __table_args__ = (
        Index('idx_sale_date', 'date'),
        Index('idx_sale_product_date', 'product_id', 'date'),
    )
```

---

## Примеры запросов

### Чтение данных

```python
# Получить все продукты
products = model.products().get_all()

# Получить продукт по ID
product = model.products().get_by_id(1)

# Получить все продажи за период
sales = model.sales().get_by_date("2024-01-01", "2024-01-31")

# Получить всех поставщиков
suppliers = model.suppliers().get_all()
```

### Создание данных

```python
# Создать новый продукт
product = model.products().create("Новый хлеб", 300)

# Создать продажу
sale = model.sales().create(
    product_id=1,
    product_name="Батон",
    price=250,
    quantity=5,
    discount=10,
    date="2024-01-15"
)

# Создать расход с документом
doc = model.expense_documents().create(
    date="2024-01-15",
    supplier_id=1,
    total_amount=5000
)

model.expense_documents().add_item(
    document_id=doc.id,
    expense_type_id=1,
    stock_item_id=1,
    quantity=100,
    price=50
)
```

### Обновление данных

```python
# Обновить цену продукта
model.products().update(1, "Батон", 280)

# Обновить количество на складе
model.stock().update(1, 150)
```

### Удаление данных

```python
# Удалить продукт (если нет связанных данных)
model.products().delete("Батон")

# Удалить документ расхода (с каскадным удалением items)
model.expense_documents().delete(1)
```

---

## Важные правила

### 1. Foreign Key Constraints

- **CASCADE DELETE:** При удалении родительской записи удаляются все дочерние
  - ExpenseDocument → ExpenseItem
  - Order → OrderItem

- **RESTRICT:** Удаление запрещено, если есть ссылающиеся записи
  - Unit → StockItem (нельзя удалить единицу, если она используется)

### 2. Целостность данных

```python
# Проверка перед удалением
can_delete = model.stock().can_delete("Мука")
if not can_delete:
    raise ValueError("Нельзя удалить - используется в рецептах")
```

### 3. Транзакции

```python
from sql_model.database import SessionLocal

db = SessionLocal()
try:
    # Несколько операций
    model.products().create("Новый продукт", 500)
    model.sales().create(...)
    model.stock().update(...)
    
    db.commit()  # Все сразу
except Exception as e:
    db.rollback()  # Отмена всех операций
    raise
finally:
    db.close()
```

---

## Рекомендации по развитию

1. **Миграции:** Используй Alembic для управления миграциями БД
2. **Кэширование:** Добавь Redis для кэширования часто используемых запросов
3. **Логирование:** Логируй все изменения в отдельную таблицу
4. **Аудит:** Отслеживай, кто и когда изменил данные
5. **Резервные копии:** Регулярно сохраняй БД

---

## Контрольный список для нового разработчика

- [ ] Понимаю структуру таблиц и связей между ними
- [ ] Знаю, как создать новую сущность
- [ ] Знаю, как добавить новое поле
- [ ] Знаю, как создать новый репозиторий
- [ ] Знаю, как добавить индекс
- [ ] Знаю, как работать с транзакциями
- [ ] Знаю, как избежать каскадного удаления нужных данных
- [ ] Знаю, как писать запросы через ORM
- [ ] Знаю, как использовать model.calculate_* методы
- [ ] Знаю, как обрабатывать ошибки целостности данных

---

**Последнее обновление:** 2024-01-18  
**Версия:** 1.0
