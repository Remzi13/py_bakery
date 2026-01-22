# ⚡ Быстрая справка (Cheat Sheet)

## Запуск приложения

```bash
# Запустить веб-сервер
python main.py
# или
python -m uvicorn main:app --reload

# Запустить с одной окном (с reload)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Инициализация БД

```python
from sql_model.database import init_db
init_db()  # Создаст таблицы и справочные данные
```

## Основные операции

### Создать объект Model

```python
from sql_model.model import SQLAlchemyModel
model = SQLAlchemyModel()
# ... работа с моделью
model.close()
```

### CRUD для каждой сущности

```python
# ========== PRODUCTS ==========
model.products().create("Батон", 250)
model.products().get_by_id(1)
model.products().get_by_name("Батон")
model.products().get_all()
model.products().update(1, "Батон", 300)
model.products().delete("Батон")

# ========== STOCK ==========
model.stock().create("Мука", "Materials", 50, "kg")
model.stock().get_by_id(1)
model.stock().get_by_name("Мука")
model.stock().get_all()
model.stock().update_quantity(1, 45)
model.stock().delete("Мука")
model.stock().can_delete("Мука")  # Проверка перед удалением

# ========== SALES ==========
model.sales().create(
    product_id=1,
    product_name="Батон",
    price=250,
    quantity=5,
    discount=10,
    date="2024-01-15"
)
model.sales().get_all()
model.sales().get_by_date("2024-01-01", "2024-01-31")

# ========== SUPPLIERS ==========
model.suppliers().create("ООО Мука", "+7-999-123-45-67")
model.suppliers().get_by_id(1)
model.suppliers().get_by_name("ООО Мука")
model.suppliers().get_all()
model.suppliers().update(1, "ООО Мука и Зерно", "+7-999-999-99-99")
model.suppliers().delete("ООО Мука")

# ========== EXPENSE TYPES ==========
model.expense_types().create("Мука", 20.0, "Raw Materials", True)
model.expense_types().get_by_id(1)
model.expense_types().get_by_name("Мука")
model.expense_types().get_all()
model.expense_types().update(1, "Мука", 25.0, "Raw Materials", True)
model.expense_types().delete(1)

# ========== EXPENSE DOCUMENTS ==========
doc = model.expense_documents().create(
    date="2024-01-15",
    supplier_id=1,
    total_amount=1000.0
)
model.expense_documents().get_by_id(1)
model.expense_documents().get_all()
model.expense_documents().add_item(
    document_id=1,
    expense_type_id=1,
    stock_item_id=1,
    quantity=50,
    price=20
)
model.expense_documents().delete(1)

# ========== WRITEOFFS ==========
model.writeoffs().create(
    product_id=1,
    quantity=5,
    reason="Брак",
    date="2024-01-15"
)
model.writeoffs().get_all()

# ========== ORDERS ==========
order = model.orders().create(
    created_date="2024-01-15",
    status="pending"
)
model.orders().add_item(
    order_id=1,
    product_id=1,
    product_name="Батон",
    quantity=50,
    price=250
)
model.orders().get_by_id(1)
model.orders().get_all()
model.orders().get_pending()
model.orders().mark_completed(1, "2024-01-20")
model.orders().delete(1)
```

## Расчеты

```python
income = model.calculate_income()      # Общий доход
expenses = model.calculate_expenses()  # Общие расходы
profit = model.calculate_profit()      # Прибыль
```

## Типы ошибок

```python
from sqlalchemy.exc import IntegrityError

try:
    model.products().create("Батон", 250)
except IntegrityError:
    print("Продукт с таким именем уже существует!")
except ValueError:
    print("Ошибка валидации данных")
except Exception as e:
    print(f"Неизвестная ошибка: {e}")
```

## FastAPI основы

### В роутере

```python
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_model

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
def list_all(model = Depends(get_model)):
    return model.products().get_all()

@router.post("/", status_code=201)
def create_one(name: str, price: float, model = Depends(get_model)):
    return model.products().create(name, price)

@router.delete("/{product_name}")
def delete_one(product_name: str, model = Depends(get_model)):
    try:
        model.products().delete(product_name)
        return {"status": "deleted"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
```

## SQL запросы (если нужны)

```python
from sqlalchemy import text, func

# Raw SQL
result = model.db.execute(text("SELECT COUNT(*) FROM products"))
count = result.scalar()

# ORM запросы
from sql_model.entities import Product
all_products = model.db.query(Product).all()
expensive = model.db.query(Product).filter(Product.price > 300).all()
```

## Отладка

```python
# Включить логирование SQL
from sql_model.database import engine
engine.echo = True

# Breakpoint для дебагинга
breakpoint()

# Вывести объект
print(repr(product))
print(product.__dict__)

# Проверить все атрибуты
from inspect import getmembers
print(getmembers(product))
```

## Структура БД в коде

```python
# Добавить поле
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    # Новое поле:
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

# Добавить связь
class Product(Base):
    # ... поля
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product")
```

## API запросы (curl)

```bash
# Получить все продукты
curl http://localhost:8000/products

# Создать продукт
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{"name":"Батон","price":250}'

# Обновить продукт
curl -X PUT "http://localhost:8000/products/1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Батон белый","price":300}'

# Удалить продукт
curl -X DELETE "http://localhost:8000/products/Батон"

# Получить статус здоровья
curl http://localhost:8000/health
```

## Важные файлы

| Файл | Назначение |
|------|-----------|
| `sql_model/database.py` | Подключение к БД |
| `sql_model/entities.py` | Модели таблиц |
| `sql_model/model.py` | Главный класс Model |
| `repositories/*.py` | Бизнес-логика |
| `api/routers/*.py` | API endpoints |
| `main.py` | FastAPI приложение |
| `DATABASE_ARCHITECTURE.md` | Полная документация БД |
| `DEVELOPER_GUIDE.md` | Примеры использования |

## Код на ошибку?

```python
# Проверь:
1. Вводы ли поле в БД или нет?
   → Посмотри sql_model/entities.py

2. Есть ли метод в репозитории?
   → Посмотри repositories/имя.py

3. Есть ли route в API?
   → Посмотри api/routers/имя.py

4. Правильный ли endpoint?
   → Проверь в @router.get/post/put/delete(...)

5. Какие ошибки?
   → Включи engine.echo = True для SQL логов
```

## Чек-лист перед commit

- [ ] Работают все CRUD операции
- [ ] Нет SQL ошибок (проверь лог)
- [ ] Внешние ключи на месте (FK constraints)
- [ ] Нет дублирования уникальных полей (UNIQUE)
- [ ] Проверены граничные случаи (null, empty strings)
- [ ] Написаны тесты
- [ ] Обновлена документация
- [ ] Нет неиспользуемого кода

## Полезные команды

```bash
# Запустить тесты
pytest tests/

# Проверить синтаксис
python -m py_compile main.py

# Форматировать код
black .

# Проверить типы
mypy .

# Сгенерировать миграцию (если используешь Alembic)
alembic revision --autogenerate -m "Описание"
alembic upgrade head
```

---

**Больше информации:** смотри [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) и [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
