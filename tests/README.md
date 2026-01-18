# Тесты для Bakery Manager API

## Описание

Этот каталог содержит полный набор тестов pytest для приложения Bakery Manager API. Тесты покрывают все основные модули приложения, включая репозитории, API маршруты и интеграцию с базой данных.

## Структура тестов

Тесты организованы по модулям приложения:

### `conftest.py`
Конфигурация pytest и глобальные фиксtures:
- `test_db` - тестовая база данных в памяти (SQLite)
- `client` - тестовый клиент FastAPI для API тестирования

### `test_products.py`
Тесты для товаров:
- `TestProductsRepository` - тесты репозитория товаров
- `TestProductsRouter` - тесты API маршрутов товаров

### `test_stock.py`
Тесты для складских запасов:
- `TestStockRepository` - тесты репозитория складских запасов
- `TestStockRouter` - тесты API маршрутов складских запасов

### `test_sales.py`
Тесты для продаж:
- `TestSalesRepository` - тесты репозитория продаж
- `TestSalesRouter` - тесты API маршрутов продаж

### `test_expenses.py`
Тесты для расходов:
- `TestExpenseTypesRepository` - тесты репозитория типов расходов
- `TestExpenseDocumentsRepository` - тесты репозитория документов расходов
- `TestExpensesRouter` - тесты API маршрутов расходов

### `test_suppliers.py`
Тесты для поставщиков:
- `TestSuppliersRepository` - тесты репозитория поставщиков
- `TestSuppliersRouter` - тесты API маршрутов поставщиков

### `test_writeoffs.py`
Тесты для списаний:
- `TestWriteOffsRepository` - тесты репозитория списаний
- `TestWriteOffsRouter` - тесты API маршрутов списаний

### `test_orders.py`
Тесты для заказов:
- `TestOrdersRepository` - тесты репозитория заказов
- `TestOrdersRouter` - тесты API маршрутов заказов

### `test_utils.py`
Тесты для утилит и справочников:
- `TestUtilsRepository` - тесты репозитория справочников

### `test_database.py`
Тесты интеграции с базой данных:
- `TestDatabaseIntegration` - тесты инициализации БД и сущностей

### `test_main.py`
Тесты основного приложения:
- `TestMainRoutes` - тесты основных маршрутов
- `TestApplicationStructure` - тесты структуры приложения
- `TestErrorHandling` - тесты обработки ошибок

## Запуск тестов

### Запустить все тесты
```bash
pytest
```

### Запустить тесты с подробным выводом
```bash
pytest -v
```

### Запустить тесты с покрытием кода
```bash
pytest --cov=. --cov-report=html
```

### Запустить тесты для конкретного модуля
```bash
pytest tests/test_products.py -v
```

### Запустить тесты с определённым паттерном имени
```bash
pytest -k "test_add" -v
```

### Запустить с остановкой на первой ошибке
```bash
pytest -x
```

### Запустить с параллельной обработкой (требует pytest-xdist)
```bash
pytest -n auto
```

## Установка зависимостей для тестирования

Убедитесь, что все зависимости установлены:

```bash
pip install -r requirements.txt
pip install pytest-cov pytest-xdist
```

## Особенности тестов

### Изолированная база данных
Каждый тест использует свежую in-memory SQLite базу данных, что обеспечивает полную изоляцию тестов.

### Фиксtures для подготовки данных
Фиксtures используются для подготовки тестовых данных:
- `setup_stock_items` - создаёт складские товары
- `setup_categories_and_units` - создаёт категории и единицы
- `setup_products_and_stock` - создаёт товары и запасы
- `setup_expense_data` - создаёт расходы

### Тестирование репозиториев
Каждый репозиторий тестируется с помощью:
- Добавления новых записей
- Получения записей по различным критериям
- Обновления и удаления записей

### Тестирование API
API маршруты тестируются с помощью TestClient:
- Проверка статус кодов ответов
- Проверка содержимого JSON ответов
- Проверка отработки HTML шаблонов

## Примеры тестов

### Простой тест репозитория
```python
def test_add_product(self, test_db: Session, setup_stock_items):
    """Test adding a new product."""
    repo = ProductsRepository(test_db)
    
    materials = [{'name': 'Flour', 'quantity': 500.0}]
    repo.add('Bread', 250, materials)
    
    product = repo.by_name('Bread')
    assert product is not None
    assert product.name == 'Bread'
```

### Тест API маршрута
```python
def test_get_products_empty(self, client, test_db: Session):
    """Test getting products when none exist."""
    response = client.get("/api/products/")
    assert response.status_code == 200
    assert response.json() == []
```

## Отладка тестов

### Запуск одного теста в режиме отладки
```bash
pytest tests/test_products.py::TestProductsRepository::test_add_new_product -v -s
```

### Вывод print() в консоль
```bash
pytest tests/test_products.py -s
```

### Пошаговое выполнение с pdb
```bash
pytest tests/test_products.py --pdb
```

## Покрытие кода

Для проверки покрытия кода тестами:

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

Отчёт об HTML покрытии будет сохранён в папке `htmlcov/`.

## Известные проблемы

1. Некоторые маршруты могут требовать дополнительной настройки для тестирования HTMX запросов.
2. Статические файлы не доступны при тестировании (нормальное поведение для unit тестов).

## Добавление новых тестов

При добавлении новых функций добавьте соответствующие тесты:

1. Создайте класс `Test<FeatureName>Repository` для тестов репозитория
2. Создайте класс `Test<FeatureName>Router` для тестов API
3. Используйте фиксtures для подготовки данных
4. Проверяйте результаты с помощью assert

Пример:
```python
class TestNewFeature:
    """Test new feature repository."""
    
    def test_new_feature_method(self, test_db: Session):
        """Test new feature method."""
        repo = NewFeatureRepository(test_db)
        result = repo.new_method()
        assert result is not None
```

## Контакты и поддержка

При вопросах о тестировании смотрите документацию FastAPI и pytest.
