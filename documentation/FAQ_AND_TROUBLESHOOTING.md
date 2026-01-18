# ❓ FAQ и решение типичных проблем

## Часто задаваемые вопросы

### Вопрос: Где начать, если я новичок?
**Ответ:**
1. Прочитай [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) - поймешь как устроена БД
2. Посмотри [DIAGRAMS_AND_EXAMPLES.md](DIAGRAMS_AND_EXAMPLES.md) - увидишь примеры потока данных
3. Используй [QUICK_REFERENCE.md](QUICK_REFERENCE.md) как шпаргалку
4. Практикуйся в [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

### Вопрос: Как быстро найти нужный метод?
**Ответ:**
Используй эту таблицу:

| Что нужно | Где искать |
|----------|-----------|
| Создать объект | `model.entity().create(...)` |
| Получить по ID | `model.entity().get_by_id(id)` |
| Получить по имени | `model.entity().get_by_name(name)` |
| Получить все | `model.entity().get_all()` |
| Обновить | `model.entity().update(id, ...)` |
| Удалить | `model.entity().delete(...)` |

---

### Вопрос: Как работает система когда я добавляю продажу?
**Ответ:**
Смотри [DIAGRAMS_AND_EXAMPLES.md](DIAGRAMS_AND_EXAMPLES.md) → раздел "Как добавляется продукт".
Процесс аналогичен для других сущностей.

---

### Вопрос: Почему я не могу удалить муку со склада?
**Ответ:**
Потому что `stock.can_delete("Мука")` вернул `False`.

Это значит, что мука используется где-то (в рецептах, продажах и т.д.).

Решение:
```python
can_delete = model.stock().can_delete("Мука")
if not can_delete:
    print("Нельзя удалить - используется в других местах")
    # Удали эти ссылки сначала
```

---

### Вопрос: Как я узнаю, что добавил правильно?
**Ответ:**
1. Проверь возвращаемый объект имеет `id`
2. Попробуй получить его обратно
3. Включи SQL логирование

```python
from sql_model.database import engine
engine.echo = True  # Показывает все SQL запросы

product = model.products().create("Батон", 250)
found = model.products().get_by_name("Батон")
assert found.id == product.id
print("✓ Успешно!")
```

---

## Типичные ошибки и решения

### ❌ IntegrityError: UNIQUE constraint failed

```
Ошибка: IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: products.name
```

**Причина:** Пытаешься создать продукт с таким же именем, который уже существует.

**Решение:**
```python
# ❌ НЕПРАВИЛЬНО
model.products().create("Батон", 250)
model.products().create("Батон", 300)  # ← ОШИБКА!

# ✅ ПРАВИЛЬНО - проверить сначала
existing = model.products().get_by_name("Батон")
if existing:
    # Обновить вместо создания
    model.products().update(existing.id, "Батон", 300)
else:
    # Создать новый
    model.products().create("Батон", 300)
```

---

### ❌ FOREIGN KEY constraint failed

```
Ошибка: sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

**Причина:** Пытаешься создать запись с несуществующим ID из другой таблицы.

**Пример:**
```python
# ❌ НЕПРАВИЛЬНО - нет поставщика с ID=999
model.expense_documents().create(
    date="2024-01-15",
    supplier_id=999,  # ← Этого поставщика не существует!
    total_amount=1000
)

# ✅ ПРАВИЛЬНО - проверить сначала
supplier = model.suppliers().get_by_id(1)
if supplier:
    model.expense_documents().create(
        date="2024-01-15",
        supplier_id=supplier.id,
        total_amount=1000
    )
else:
    print("Поставщик не найден!")
```

---

### ❌ ValueError: Product not found

```
Ошибка: ValueError: Product 999 not found
```

**Причина:** Пытаешься обновить или удалить объект, который не существует.

**Решение:**
```python
# ❌ НЕПРАВИЛЬНО
model.products().update(999, "Батон", 300)  # ← ОШИБКА!

# ✅ ПРАВИЛЬНО
product = model.products().get_by_id(999)
if product:
    model.products().update(999, "Батон", 300)
else:
    print("Продукт не найден!")
```

---

### ❌ TypeError: unsupported operand type(s) for *

```
Ошибка: TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'
```

**Причина:** Получил `None` вместо объекта, попробовал с ним работать.

**Решение:**
```python
# ❌ НЕПРАВИЛЬНО
product = model.products().get_by_id(999)
income = product.price * 100  # product = None, ошибка!

# ✅ ПРАВИЛЬНО
product = model.products().get_by_id(999)
if product:
    income = product.price * 100
else:
    print("Продукт не найден!")
```

---

### ❌ AttributeError: 'Product' object has no attribute

```
Ошибка: AttributeError: 'Product' object has no attribute 'description'
```

**Причина:** Пытаешься обратиться к полю, которого нет в модели.

**Решение:**
1. Проверь название поля в `sql_model/entities.py`
2. Если поля нет - добавь его туда
3. Пересоздай БД

```python
# В sql_model/entities.py
class Product(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    # Добавь новое поле:
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

---

### ❌ SQLAlchemy MappingError

```
Ошибка: sqlalchemy.exc.InvalidRequestError: One or more mappers failed
```

**Причина:** Синтаксическая ошибка в определении модели.

**Решение:**
1. Проверь синтаксис в `sql_model/entities.py`
2. Убедись что все импорты на месте
3. Запусти через Python IDE с проверкой синтаксиса

```python
# ✅ Правильно
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, List

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # ... остальные поля
```

---

## Проблемы с базой данных

### ❌ БД не создается

**Проверка:**
```bash
# 1. Убедись что нет ошибок при инициализации
python -c "from sql_model.database import init_db; init_db(); print('OK')"

# 2. Проверь что БД создалась
ls -la bakery_management.db
```

**Решение:**
```python
# В main.py или test скрипте
from sql_model.database import init_db, engine
from sql_model.entities import Base

# Пересоздать БД с нуля
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
init_db()
```

---

### ❌ БД заблокирована

```
Ошибка: sqlite3.OperationalError: database is locked
```

**Причина:** Несколько процессов одновременно пишут в БД.

**Решение:**
1. Закрой все запущенные приложения
2. Удали лишние подключения
3. Добавь timeout в database.py

```python
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Увеличить timeout
    }
)
```

---

### ❌ Потеря данных при пересоздании БД

**Проблема:** Пересоздал БД, все данные потеряны.

**Решение:**
```python
# Перед пересозданием сделай backup
import shutil
from datetime import datetime

backup_name = f"bakery_management.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy("bakery_management.db", backup_name)
print(f"✓ Backup создан: {backup_name}")

# Теперь можешь пересоздать БД
```

---

## Проблемы с API

### ❌ HTTP 404: endpoint not found

```
Ошибка: 404 Not Found
```

**Причина:** Endpoint не подключен в `main.py` или маршрут неправильный.

**Решение:**
```python
# В main.py
from api.routers import products

# Проверь что это есть:
app.include_router(products.router)

# Проверь prefix в роутере:
router = APIRouter(prefix="/products", tags=["products"])
```

---

### ❌ HTTP 422: validation error

```
Ошибка: {"detail":[{"loc":["body","name"],"msg":"field required"}]}
```

**Причина:** Не отправил требуемое поле в JSON.

**Решение:**
```bash
# ❌ НЕПРАВИЛЬНО
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{"price":250}'  # ← Забыл name!

# ✅ ПРАВИЛЬНО
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{"name":"Батон","price":250}'
```

---

### ❌ HTTP 500: internal server error

```
Ошибка: Internal Server Error
```

**Решение:**
1. Посмотри логи FastAPI в консоли
2. Добавь исключение в роутер
3. Логируй ошибки

```python
@router.post("/")
def create_product(data: ProductCreate, model = Depends(get_model)):
    try:
        return model.products().create(data.name, data.price)
    except Exception as e:
        import traceback
        traceback.print_exc()  # Вывести полный stacktrace
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Проблемы с производительностью

### ❌ Запрос очень медленный

**Решение:**
1. Добавь индекс
2. Используй `.limit()` для больших таблиц
3. Логируй SQL запросы

```python
# Включи SQL логирование
from sql_model.database import engine
engine.echo = True

# Посмотри какой запрос выполняется
# Добавь индекс если нужно

from sqlalchemy import Index
class Sale(Base):
    __table_args__ = (
        Index('idx_sale_date', 'date'),
    )
```

---

### ❌ Слишком много памяти

**Решение:**
```python
# ❌ НЕПРАВИЛЬНО - загружает все в памяти
all_sales = model.sales().get_all()

# ✅ ПРАВИЛЬНО - использует pagination
sales = model.db.query(Sale).limit(100).all()
```

---

## Проблемы с тестированием

### ❌ Тесты используют настоящую БД

**Решение:**
```python
# conftest.py
import pytest
import tempfile
from sql_model.database import SessionLocal, init_db, engine, DATABASE_URL
from sql_model.entities import Base

@pytest.fixture
def test_db():
    """Создать временную БД для тестов."""
    # Использовать временный файл вместо настоящей БД
    test_db_path = tempfile.mktemp()
    test_engine = create_engine(f"sqlite:///{test_db_path}")
    
    Base.metadata.create_all(test_engine)
    
    session = SessionLocal(bind=test_engine)
    yield session
    
    session.close()
    # Cleanup
    import os
    os.remove(test_db_path)
```

---

## Полезные отладочные команды

### Вывести все таблицы в БД
```python
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(tables)
# Результат: ['products', 'stock', 'sales', ...]
```

### Вывести структуру таблицы
```python
from sqlalchemy import inspect
inspector = inspect(engine)
columns = inspector.get_columns('products')
for col in columns:
    print(f"{col['name']}: {col['type']}")
# Результат:
# id: INTEGER
# name: VARCHAR
# price: INTEGER
```

### Проверить все индексы
```python
from sqlalchemy import inspect
inspector = inspect(engine)
indexes = inspector.get_indexes('products')
for idx in indexes:
    print(f"Index: {idx['name']}, Columns: {idx['column_names']}")
```

### Вывести все связи (relationships)
```python
from sqlalchemy import inspect
mapper = inspect(Product)
for relationship in mapper.relationships:
    print(f"{relationship.key}: {relationship.mapper.class_}")
```

---

## Контрольный список для отладки

Когда что-то не работает, проверь:

- [ ] БД инициализирована (`init_db()` был вызван)?
- [ ] Объект существует в БД (`get_by_id()` вернул не None)?
- [ ] ID правильный (число, не строка)?
- [ ] Внешние ключи корректные (referenced объекты существуют)?
- [ ] SQL логирование включено (`engine.echo = True`)?
- [ ] Model закрыт после использования (`model.close()`)?
- [ ] Правильное имя метода репозитория?
- [ ] Правильный prefix в роутере?
- [ ] Роутер подключен в main.py?
- [ ] FastAPI запущен без ошибок?

---

## Быстрые команды для отладки

```bash
# Проверить что приложение стартует
python main.py
# или
python -m uvicorn main:app --reload

# Проверить БД
python -c "from sql_model.database import init_db; init_db(); print('✓ DB OK')"

# Запустить тесты
pytest tests/ -v

# Проверить синтаксис
python -m py_compile main.py

# Форматировать код
black .

# Проверить типы (если используешь type hints)
mypy .
```

---

## Когда ничего не помогает

1. **Удали БД и пересоздай:**
   ```bash
   rm bakery_management.db
   python -c "from sql_model.database import init_db; init_db()"
   ```

2. **Перезагрузи Python интерпретатор**

3. **Проверь свежесть кода:**
   ```bash
   git status
   git diff
   ```

4. **Обнови зависимости:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

5. **Найди ошибку через print():**
   ```python
   print(f"DEBUG: product = {product}")
   print(f"DEBUG: product.id = {product.id if product else 'None'}")
   ```

6. **Используй debugger:**
   ```python
   breakpoint()  # Приостановит выполнение
   ```

7. **Посмотри issue на GitHub или StackOverflow**

---

## 📞 Куда ещё смотреть

| Проблема | Документ |
|---------|----------|
| Структура БД | [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) |
| Примеры кода | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |
| Быстрая справка | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| Диаграммы | [DIAGRAMS_AND_EXAMPLES.md](DIAGRAMS_AND_EXAMPLES.md) |
| Обзор документации | [DOCUMENTATION.md](DOCUMENTATION.md) |

---

**Помните:** Лучший способ отладки - это медленное, внимательное чтение кода и логов.

Включи логирование, перепроверь синтаксис, вспомни что изменял в последний раз.

99% ошибок - это опечатки или пропущенные скобки! 😅
