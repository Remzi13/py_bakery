# ⚡ 5-минутный старт для нетерпеливых

Если у тебя есть 5 минут - это для тебя!

## Запуск проекта

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Запустить
python main.py

# 3. Открыть браузер
http://localhost:8000
```

## Первый код за 1 минуту

```python
from sql_model.model import SQLAlchemyModel

# Создать объект БД
model = SQLAlchemyModel()

# Создать продукт
product = model.products().create("Батон", 250)
print(f"✓ Создан: {product.name}, ID: {product.id}")

# Получить все продукты
all_products = model.products().get_all()
print(f"Всего продуктов: {len(all_products)}")

# Закрыть
model.close()
```

Результат:
```
✓ Создан: Батон, ID: 1
Всего продуктов: 1
```

## Основные операции

```python
model = SQLAlchemyModel()

# СОЗДАТЬ
product = model.products().create("Батон", 250)
stock = model.stock().create("Мука", "Materials", 50, "kg")
sale = model.sales().create(1, "Батон", 250, 5, 0, "2024-01-15")

# ПОЛУЧИТЬ
one = model.products().get_by_id(1)
one = model.products().get_by_name("Батон")
all = model.products().get_all()

# ОБНОВИТЬ
model.products().update(1, "Батон", 300)

# УДАЛИТЬ
model.products().delete("Батон")

# РАСЧЕТЫ
income = model.calculate_income()
expenses = model.calculate_expenses()
profit = model.calculate_profit()

model.close()
```

## API запросы

```bash
# Получить все продукты
curl http://localhost:8000/products

# Создать продукт
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Батон","price":250}'

# Обновить
curl -X PUT http://localhost:8000/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Батон","price":300}'

# Удалить
curl -X DELETE http://localhost:8000/products/Батон
```

## Таблицы БД (13 штук)

| # | Таблица | Что | Пример |
|---|---------|-----|---------|
| 1 | **Products** | Готовые товары | Батон (250 price) |
| 2 | **Stock** | Запасы | Мука (50 kg) |
| 3 | **Sales** | Продажи | Продал 5 батонов |
| 4 | **Orders** | Заказы | Заказ на 50 батонов |
| 5 | **Suppliers** | Поставщики | ООО Мука |
| 6 | **ExpenseDocuments** | Счета | Счет за муку 2000 |
| 7 | **Units** | Единицы | kg, l, piece |
| 8 | **Stock Categories** | Категории | Materials, Packaging |
| 9 | **Expense Types** | Типы расходов | Мука, электричество |
| 10 | **Expense Categories** | Категории расходов | Raw Materials, Utilities |
| 11 | **Expense Items** | Строки счетов | Мука 50kg × 20 |
| 12 | **Write-offs** | Списания | Списал 5 батонов (брак) |
| 13 | **Order Items** | Позиции заказов | Батон × 50 шт |

## Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `UNIQUE constraint failed` | Это имя уже существует |
| `FOREIGN KEY constraint failed` | Referenced объект не существует |
| `Product not found` | ID неправильный или объект удален |
| `database is locked` | Закрой другие подключения к БД |
| `404 Not Found` | Endpoint не подключен в main.py |

## Полезные команды

```bash
# Запустить тесты
pytest tests/ -v

# Форматировать код
black .

# Проверить синтаксис
python -m py_compile main.py

# Удалить и пересоздать БД
rm bakery_management.db
python -c "from sql_model.database import init_db; init_db()"

# Посмотреть все таблицы в БД
python -c "from sqlalchemy import inspect; from sql_model.database import engine; print(inspect(engine).get_table_names())"
```

## Структура проекта (самое важное)

```
py_bakery/
├── main.py                    # FastAPI приложение
├── sql_model/
│   ├── database.py           # Подключение
│   ├── entities.py           # Модели (таблицы)
│   └── model.py              # Главный класс
├── repositories/             # Бизнес-логика
├── api/routers/              # API endpoints
├── templates/                # HTML
├── static/                   # CSS, JS
├── tests/                    # Тесты
└── [ДОКУМЕНТАЦИЯ]
    ├── INDEX.md              # ← ГЛАВНЫЙ ИНДЕКС
    ├── DOCUMENTATION.md      # ← НАЧНИ ОТСЮДА
    ├── DATABASE_ARCHITECTURE.md
    ├── DEVELOPER_GUIDE.md
    ├── QUICK_REFERENCE.md
    ├── DIAGRAMS_AND_EXAMPLES.md
    ├── FAQ_AND_TROUBLESHOOTING.md
    └── 5_MINUTE_START.md     # ← ТЫ ЗДЕСЬ
```

## Быстрые ссылки

- 🎯 **Главный индекс:** [INDEX.md](INDEX.md)
- 📚 **Полная документация:** [DOCUMENTATION.md](DOCUMENTATION.md)
- 📋 **Архитектура БД:** [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)
- 🔧 **Примеры кода:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- ⚡ **Быстрая справка:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 📊 **Диаграммы:** [DIAGRAMS_AND_EXAMPLES.md](DIAGRAMS_AND_EXAMPLES.md)
- ❓ **FAQ и ошибки:** [FAQ_AND_TROUBLESHOOTING.md](FAQ_AND_TROUBLESHOOTING.md)

## Сценарии

### Хочу добавить продукт
```python
model.products().create("Название", цена)
```

### Хочу записать продажу
```python
model.sales().create(
    product_id=1,
    product_name="Батон",
    price=250,
    quantity=5,
    discount=0,
    date="2024-01-15"
)
```

### Хочу посчитать доход
```python
income = model.calculate_income()
```

### Хочу добавить API
Смотри файл `api/routers/products.py` - скопируй и адаптируй!

### Хочу создать новую таблицу
1. Добавь класс в `sql_model/entities.py`
2. Создай репозиторий в `repositories/`
3. Добавь в `sql_model/model.py`
4. Создай роутер в `api/routers/`
5. Удали старую БД - создается новая!

## Отладка в 30 секунд

```python
# Включи SQL логирование
from sql_model.database import engine
engine.echo = True

# Теперь будут видны все SQL запросы!

# Или используй breakpoint
breakpoint()  # Приостановит выполнение, можешь исследовать переменные
```

## Когда что-то не работает

1. Посмотри логи в консоли
2. Включи `engine.echo = True`
3. Используй `print()` для отладки
4. Посмотри в [FAQ_AND_TROUBLESHOOTING.md](FAQ_AND_TROUBLESHOOTING.md)

## Память на 1 минуту

- **13 таблиц** - Products, Stock, Sales, Orders, Suppliers, ...
- **3 метода CRUD** - create(), get_by_id(), update(), delete()
- **1 главный класс** - SQLAlchemyModel
- **1 главный файл БД** - bakery_management.db
- **Всегда закрывай** - model.close()

---

**Помощь:**
- Забыл синтаксис? → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Нужен пример? → [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- Что-то сломалось? → [FAQ_AND_TROUBLESHOOTING.md](FAQ_AND_TROUBLESHOOTING.md)

**Готов углубляться?** → Смотри [DOCUMENTATION.md](DOCUMENTATION.md)

---

**Время создания:** 2024-01-18  
**Для полноты:** Прочитай [DOCUMENTATION.md](DOCUMENTATION.md) (5 мин)
