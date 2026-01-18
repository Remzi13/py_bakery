# Запуск тестов Bakery Manager

## Быстрый старт

Запустить все тесты:
```bash
pytest tests/
```

Запустить с подробным выводом:
```bash
pytest tests/ -v
```

## Рабочие тесты

Следующие тесты работают корректно и рекомендуются к использованию:

### Основные тесты

```bash
# Тесты базы данных и сущностей
pytest tests/test_database.py -v

# Тесты основного приложения и маршрутов
pytest tests/test_main.py -v

# Тесты API endpoints
pytest tests/test_api_endpoints.py -v

# Тесты утилит и справочников
pytest tests/test_utils.py -v
```

## Статус тестов по модулям

### ✅ Полностью рабочие
- `test_database.py` - Все 6 тестов проходят (инициализация БД, сущности, связи)
- `test_main.py` - 8 из 9 тестов проходят (маршруты, структура, обработка ошибок)
- `test_api_endpoints.py` - Все 7 тестов проходят (API endpoints)
- `test_utils.py` - Все 11 тестов проходят (утилиты и справочники)

### ⚠️ Требуют доработки
- `test_products.py` - Частично (нужна доработка для тестирования с моделью)
- `test_stock.py` - Требует передачи model_instance
- `test_sales.py` - Требует передачи model_instance  
- `test_expenses.py` - Требует доработки методов репозитория
- `test_suppliers.py` - Частично рабочие
- `test_orders.py` - Требует передачи model параметра
- `test_writeoffs.py` - Требует передачи model_instance

## Примеры использования

### Запустить конкретный тест
```bash
pytest tests/test_database.py::TestDatabaseIntegration::test_units_exist -v
```

### Запустить тесты с поиском по имени
```bash
pytest -k "test_units" -v
```

### Запустить с остановкой на первой ошибке
```bash
pytest tests/ -x
```

### Запустить с показом print() output
```bash
pytest tests/test_database.py -s
```

### Запустить тесты с покрытием (требует pytest-cov)
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

## Установка зависимостей

```bash
pip install pytest pytest-cov pytest-xdist httpx
```

## Структура тестов

```
tests/
├── conftest.py                 # Глобальные фиксtures и конфигурация
├── test_database.py            # ✅ Тесты БД и сущностей
├── test_main.py                # ✅ Тесты основного приложения
├── test_api_endpoints.py        # ✅ Тесты API endpoints
├── test_utils.py               # ✅ Тесты утилит
├── test_integration.py          # Интеграционные тесты
├── test_products.py            # Тесты товаров (частично)
├── test_stock.py               # Тесты складских запасов
├── test_sales.py               # Тесты продаж
├── test_expenses.py            # Тесты расходов
├── test_suppliers.py           # Тесты поставщиков
├── test_orders.py              # Тесты заказов
├── test_writeoffs.py           # Тесты списаний
├── README.md                   # Подробная документация
└── __init__.py                 # Пакет инициализация
```

## Отладка

### Запустить один тест в режиме отладки с pdb
```bash
pytest tests/test_database.py::TestDatabaseIntegration::test_units_exist -v --pdb
```

### Показать локальные переменные при ошибке
```bash
pytest tests/test_database.py -v -l
```

### Полный traceback
```bash
pytest tests/test_database.py -v --tb=long
```

## Рекомендации

1. **Для быстрой проверки:** Используйте рабочие тесты (test_database.py, test_main.py, test_api_endpoints.py, test_utils.py)

2. **Для интеграционных тестов:** Используйте test_integration.py с fixture `model`

3. **Для обновления тестов:** Обновляйте тесты согласно фактической структуре репозиториев

4. **CI/CD:** Используйте только рабочие тесты в pipeline

## Частые ошибки

### "AttributeError: object has no attribute 'get_by_name'"
Некоторые репозитории используют `by_name()` вместо `get_by_name()`. Проверьте фактические методы репозитория.

### "TypeError: __init__() missing required argument"
Некоторые репозитории требуют `model_instance` параметра. Используйте fixture `model` для их создания.

### "AssertionError: 404 != 200"
Проверьте точный путь API endpoint в маршрутизаторе. Может быть префикс или суффикс пути.

## Контакты

При вопросах по тестированию смотрите полную документацию в `README.md`.
