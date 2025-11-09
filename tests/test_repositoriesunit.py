import pytest
import sqlite3
from typing import Any


# Импорт репозиториев и вспомогательных компонентов
from sql_model.model import SQLiteModel
from sql_model.database import create_connection, initialize_db, get_unit_by_name
from repositories.expense_types import ExpenseTypesRepository
from repositories.stock import StockRepository
from repositories.ingredients import IngredientsRepository
from repositories.products import ProductsRepository
from repositories.expenses import ExpensesRepository
from repositories.sales import SalesRepository
from repositories.write_offs import WriteOffsRepository
from repositories.suppliers import SuppliersRepository
from repositories.utils import UtilsRepository


TEST_DB = ':memory:'

# --- Общие Фикстуры ---

@pytest.fixture
def conn():
    """Предоставляет чистое, инициализированное соединение с БД в памяти."""
    conn = create_connection(TEST_DB)
    initialize_db(conn)
    yield conn
    conn.close()

@pytest.fixture
def model(conn: sqlite3.Connection):
    """Предоставляет экземпляр SQLiteModel, использующий то же соединение."""
    # Мы используем SQLiteModel, чтобы корректно инициализировать все зависимости
    # и иметь доступ к вспомогательным репозиториям.
    # Фактически, мы тестируем репозитории, используя Model как Фабрику.
    return SQLiteModel(db_file=TEST_DB)


@pytest.fixture
def setup_ids(conn: sqlite3.Connection):
    """Предоставляет ID справочных сущностей для тестов."""
    return {
        'kg_id': get_unit_by_name(conn, 'кг'),
        'expense_cat_id': conn.execute("SELECT id FROM expense_categories WHERE name = 'Сырьё'").fetchone()[0],
        'stock_cat_id': conn.execute("SELECT id FROM stock_categories WHERE name = 'Сырье'").fetchone()[0]
    }


@pytest.fixture
def write_off_data(model: SQLiteModel):
    """
    Настраивает минимальные данные для тестов списаний: 
    Ингредиент 'Мука' (сырье) и Продукт 'Круассан' (с рецептом).
    Использует фикстуру model (SQLiteModel) для доступа к репозиториям.
    """
    
    # 1. Сырье/Запас (Мука)
    # model.ingredients().add() создает запись в ingredients, stock и expense_types
    model.ingredients().add(name="Мука", unit_name="кг")
    # Устанавливаем начальный запас: 10 кг
    model.stock().set("Мука", 10.0) 
    
    # 2. Продукт (Круассан) с рецептом: 0.1 кг муки на 1 шт.
    croissant = model.products().add(
        name="Круассан", 
        price=150, 
        ingredients=[{'name':"Мука", 'quantity': 0.1}] # <-- Важный рецепт для логики списания
    )
    
    # Получаем ID продукта для проверки записей в таблице списаний
    croissant_id = model.products().by_name("Круассан").id
    
    return {
        "croissant_id": croissant_id,
        "croissant_name": "Круассан",
        "flour_name": "Мука",
        "model": model # Возвращаем модель для удобства доступа в тестах
    }

@pytest.fixture
def expense_data(model: SQLiteModel) -> dict:
    """Подготавливает данные для тестов ExpensesRepository."""
    # 1. Создаем поставщиков (НОВЫЙ ШАГ)
    supplier_repo = model.suppliers()
    supplier_repo.add("Мукомольный завод №1", "Иван Иванов", "+71234567890", "ivan@mill.ru", "ул. Мельничная, 1")
    supplier_repo.add("ООО 'Упаковка'", "Петр Петров", "88001234567")
    
    # 2. Создаем типы расходов (Сырье и Платежи)
    model.expense_types().add("Мука пшеничная", 50, "Сырьё")
    model.expense_types().add("Аренда", 50000, "Платежи")
    
    # 3. Добавляем ингредиент (он автоматически создаст StockItem и ExpenseType)
    # Это важно, чтобы ExpenseTypesRepository мог найти "Мука пшеничная"
    model.ingredients().add("Мука", "кг")
    
    # 4. Добавляем несколько расходов
    # Расход, связанный с поставщиком
    model.expenses().add("Мука", 45, 100.0, supplier_name="Мукомольный завод №1")
    # Расход без поставщика
    model.expenses().add("Аренда", 50000, 1.0, supplier_name=None)
    
    # 5. Возвращаем данные для теста
    return {
        'model': model
    }

@pytest.fixture
def supplier_data(model: SQLiteModel):
    """Предоставляет инициализированный репозиторий поставщиков с тестовыми данными."""
    s_repo = model.suppliers()
    s_repo.add(name="Мука и Зерно", contact_person="Иванов И.И.", phone="555-1234")
    s_repo.add(name="Дрожжи и Добавки", contact_person="Петров П.П.")
    
    # ID для тестов
    supplier1_id = s_repo.by_name("Мука и Зерно").id
    supplier2_id = s_repo.by_name("Дрожжи и Добавки").id
    
    return {
        'model': model,
        'repo': s_repo,
        'id1': supplier1_id,
        'id2': supplier2_id
    }
# --- 1. Тесты для ExpenseTypesRepository ---

class TestExpenseTypesRepository:
    
    @pytest.fixture
    def repo(self, conn: sqlite3.Connection) -> ExpenseTypesRepository:
        return ExpenseTypesRepository(conn)

    def test_add_and_get(self, repo: ExpenseTypesRepository, setup_ids: dict, conn: sqlite3.Connection):
       
        repo.add(name='Аренда', default_price=50000, category_name='Платежи')
        expense_type = repo.get('Аренда')
        
        assert expense_type is not None
        assert expense_type.name == 'Аренда'
        assert expense_type.default_price == 50000
        
        # Теперь conn - это объект соединения, который может выполнять SQL
        assert expense_type.category_id == conn.execute("SELECT id FROM expense_categories WHERE name = 'Платежи'").fetchone()[0]
        assert repo.len() == 1
        
    def test_delete(self, repo: ExpenseTypesRepository):
        repo.add(name='Зарплата', default_price=30000, category_name='Платежи')
        assert repo.len() == 1
        
        repo.delete('Зарплата')
        assert repo.get('Зарплата') is None
        assert repo.empty() is True

    def test_data(self, repo: ExpenseTypesRepository):
        repo.add(name='Аренда', default_price=50000, category_name='Платежи')
        repo.add(name='Свет', default_price=1000, category_name='Платежи')
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Аренда'
        assert data[1].default_price == 1000

    def test_get_names_by_category_name(self, repo: ExpenseTypesRepository, setup_ids: dict):
        """
        Проверяет, что get_names_by_category_name возвращает только имена типов 
        расходов, принадлежащих указанной категории.
        """
        
        # 1. Подготовка: Добавляем типы расходов в разные категории
        # Предполагаем, что категории 'Платежи' и 'Сырьё' существуют в базе данных
        repo.add(name='Аренда', default_price=50000, category_name='Платежи')
        repo.add(name='Электричество', default_price=1000, category_name='Платежи')
        repo.add(name='Мука', default_price=50, category_name='Сырьё')
        
        # 2. Действие: Запрашиваем типы для категории 'Платежи'
        payment_names = repo.get_names_by_category_name('Платежи')
        
        # Проверка 1: Корректное количество и содержимое
        assert len(payment_names) == 2
        # Проверяем, что имена отсортированы (если мы добавили ORDER BY name в SQL)
        assert payment_names == ['Аренда', 'Электричество'] 
        
        # 3. Действие: Запрашиваем типы для категории 'Сырьё'
        ingredient_names = repo.get_names_by_category_name('Сырьё')
        
        # Проверка 2: Корректное содержимое
        assert len(ingredient_names) == 1
        assert ingredient_names[0] == 'Мука'
        
        # 4. Проверка на несуществующую категорию
        unknown_names = repo.get_names_by_category_name('Несуществующая Категория')
        assert len(unknown_names) == 0
        assert unknown_names == []

    def test_get_by_category_name(self, repo: ExpenseTypesRepository, setup_ids: dict):
        """
        Проверяет, что get_by_category_name возвращает полные объекты ExpenseType,
        отфильтрованные по имени категории.
        """
        
        # 1. Подготовка: Добавляем типы расходов в разные категории
        # Предполагаем, что категории 'Платежи' и 'Сырьё' существуют в базе данных
        repo.add(name='Аренда', default_price=50000, category_name='Платежи')
        repo.add(name='Электричество', default_price=1000, category_name='Платежи')
        repo.add(name='Мука', default_price=50, category_name='Сырьё')
        
        # 2. Действие: Запрашиваем типы для категории 'Платежи'
        payment_expenses = repo.get_by_category_name('Платежи')
        
        # Проверка 1: Корректное количество и содержимое
        assert len(payment_expenses) == 2
        
        # Проверяем, что вернулись полные объекты и они корректно отфильтрованы
        # (Сортировка по имени: 'Аренда' идет раньше 'Электричество')
        assert payment_expenses[0].name == 'Аренда'
        assert payment_expenses[0].default_price == 50000
        assert payment_expenses[1].name == 'Электричество'
        assert payment_expenses[1].default_price == 1000
        
        # 3. Действие: Запрашиваем типы для категории 'Сырьё'
        ingredient_expenses = repo.get_by_category_name('Сырьё')
        
        # Проверка 2: Корректное содержимое
        assert len(ingredient_expenses) == 1
        assert ingredient_expenses[0].name == 'Мука'
        
        # 4. Проверка на несуществующую категорию
        unknown_expenses = repo.get_by_category_name('Несуществующая Категория')
        assert len(unknown_expenses) == 0
        assert unknown_expenses == []

# --- 2. Тесты для StockRepository ---

class TestStockRepository:
    
    @pytest.fixture
    def repo(self, conn: sqlite3.Connection) -> StockRepository:
        return StockRepository(conn)

    def test_add_and_get(self, repo: StockRepository):
        repo.add(name='Мешок', category_name='Упаковка', quantity=100.0, unit_name='штук')
        item = repo.get('Мешок')
        
        assert repo.by_id(item.id).name == item.name
        assert item is not None
        assert item.name == 'Мешок'
        assert item.quantity == 100.0
        assert repo.len() == 1
        
    def test_update_quantity(self, repo: StockRepository):
        repo.add(name='Вода', category_name='Сырье', quantity=50.0, unit_name='литр')
        
        # Оприходование
        repo.update('Вода', 10.0)
        assert repo.get('Вода').quantity == 60.0
        
        # Списание
        repo.update('Вода', -20.0)
        assert repo.get('Вода').quantity == 40.0
        
    def test_update_negative_balance(self, repo: StockRepository):
        repo.add(name='Масло', category_name='Сырье', quantity=10.0, unit_name='кг')
        
        # Попытка списать больше, чем есть
        with pytest.raises(ValueError, match="Недостаточно запаса для 'Масло'. Требуется списание 100.00, текущий остаток 10.00."):
            repo.update('Масло', -100.0)

    def test_data(self, repo: StockRepository):
        repo.add(name='Мука', category_name='Сырье', quantity=100.0, unit_name='кг')
        repo.add(name='Яйцо', category_name='Сырье', quantity=50.0, unit_name='штук')
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Мука'
        assert data[1].quantity == 50.0

    def test_set_quantity(self, repo: StockRepository):
        """Проверяет, что метод set корректно устанавливает новое количество."""
    
        # 1. Подготовка: Добавляем элемент запаса
        repo.add(name='Сахар', category_name='Сырье', quantity=100.0, unit_name='кг')
    
        # 2. Действие: Устанавливаем новое количество
        repo.set('Сахар', 55.5)
    
        # 3. Проверка: Получаем элемент и проверяем его количество
        updated_item = repo.get('Сахар')
        assert updated_item.quantity == 55.5
    
        # 4. Проверка на ошибку при несуществующем элементе
        with pytest.raises(KeyError):
            repo.set('Несуществующий Товар', 10.0)

    def test_update_quantity_positive(self, repo: StockRepository):
        """Проверяет, что update корректно увеличивает запас."""
        repo.add(name='Мука', category_name='Сырье', quantity=10.0, unit_name='кг')
    
        # Увеличение (покупка)
        repo.update('Мука', 5.5)
    
        updated_item = repo.get('Мука')
        assert updated_item.quantity == 15.5

    def test_update_quantity_negative_success(self, repo: StockRepository):
        """Проверяет, что update корректно уменьшает запас при достаточном остатке."""
        repo.add(name='Мука', category_name='Сырье', quantity=10.0, unit_name='кг')

        # Уменьшение (продажа)
        repo.update('Мука', -3.0)

        updated_item = repo.get('Мука')
        assert updated_item.quantity == 7.0

    def test_update_quantity_negative_failure(self, repo: StockRepository):
        """Проверяет, что update вызывает ValueError при попытке уйти в минус."""
        repo.add(name='Мука', category_name='Сырье', quantity=10.0, unit_name='кг')

        # Попытка списания больше, чем есть на складе
        with pytest.raises(ValueError, match="Недостаточно запаса"):
            repo.update('Мука', -10.1)
        
        # Проверяем, что количество не изменилось (rollback)
        item_after_fail = repo.get('Мука')
        assert item_after_fail.quantity == 10.0

# --- 3. Тесты для IngredientsRepository (Сложная логика) ---

class TestIngredientsRepository:

    def test_add_with_relations(self, model: SQLiteModel):
        """Проверка, что добавление ингредиента создает связанные StockItem и ExpenseType."""
        repo = model.ingredients()
        
        repo.add(name='Мука', unit_name='кг')

        # 1. Проверка Ingredients
        assert repo.len() == 1
        ing = repo.by_name('Мука')
        assert ing.name == 'Мука'
        
        # 2. Проверка StockItem
        stock_item = model.stock().get('Мука')
        assert stock_item is not None
        assert stock_item.quantity == 0.0
        assert stock_item.category_id == model.stock()._get_category_id('Сырье')

        # 3. Проверка ExpenseType
        expense_type = model.expense_types().get('Мука')
        assert expense_type is not None
        assert expense_type.default_price == 100
        
    def test_delete_allowed(self, model: SQLiteModel):
        repo = model.ingredients()
        repo.add(name='Соль', unit_name='кг')
        
        # Проверка, что удаление разрешено
        assert repo.can_delete('Соль') is True
        repo.delete('Соль')
        
        assert repo.has('Соль') is False
        assert model.stock().get('Соль') is None # Проверка удаления связи

    def test_delete_denied(self, model: SQLiteModel):
        repo = model.ingredients()
        repo.add(name='Сахар', unit_name='кг')
        
        # Искусственно создаем продукт, использующий Сахар, 
        # чтобы проверить запрет на удаление.
        model.products().add(
            name='Торт', 
            price=1000, 
            ingredients=[{'name': 'Сахар', 'quantity': 0.5}]
        )
        
        # Проверка, что удаление запрещено
        assert repo.can_delete('Сахар') is False
        with pytest.raises(ValueError, match="Ингредиент 'Сахар' используется в продукте"):
            repo.delete('Сахар')
        assert repo.has('Сахар') is True
        
    def test_data(self, model: SQLiteModel):
        repo = model.ingredients()
        repo.add(name='Сахар', unit_name='кг')
        repo.add(name='Вода', unit_name='литр')
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Сахар'
        assert data[1].unit_id == 3 # ID 'литр' (при условии, что 'литр' имеет id=3)

# --- 4. Тесты для ProductsRepository (Рецепты) ---

class TestProductsRepository:

    def test_add_and_get_recipe(self, model: SQLiteModel):
        repo = model.products()
        model.ingredients().add('Мука', 'кг')
        model.ingredients().add('Вода', 'литр')

        recipe = [
            {'name': 'Мука', 'quantity': 1.5}, 
            {'name': 'Вода', 'quantity': 0.5}
        ]
        repo.add(name='Багет', price=150, ingredients=recipe)
        
        product = repo.by_name('Багет')
        assert product.price == 150
        
        # Проверка получения рецепта из связующей таблицы
        retrieved_recipe = repo.get_ingredients_for_product(product.id)
        assert len(retrieved_recipe) == 2
        assert retrieved_recipe[0]['name'] == 'Мука'
        assert retrieved_recipe[0]['quantity'] == 1.5
        
    def test_update_product_and_recipe(self, model: SQLiteModel):
        repo = model.products()
        model.ingredients().add('Мука', 'кг')
        model.ingredients().add('Соль', 'грамм')
        
        repo.add(name='Пирог', price=500, ingredients=[{'name': 'Мука', 'quantity': 1.0}])
        
        # Обновление: новая цена и новый рецепт
        new_recipe = [{'name': 'Соль', 'quantity': 5.0}]
        repo.add(name='Пирог', price=600, ingredients=new_recipe)
        
        updated_product = repo.by_name('Пирог')
        assert updated_product.price == 600
        
        # Проверка, что старый рецепт удален, а новый добавлен
        updated_recipe = repo.get_ingredients_for_product(updated_product.id)
        assert len(updated_recipe) == 1
        assert updated_recipe[0]['name'] == 'Соль'
        
    def test_delete_product(self, model: SQLiteModel):
        repo = model.products()
        repo.add(name='Кекс', price=50, ingredients=[])
        
        repo.delete('Кекс')
        assert repo.has('Кекс') is False

    def test_delete_cascades_to_recipes(self, model: SQLiteModel):
        """
        Проверяет, что при удалении продукта удаляются все его рецепты (записи в таблице recipes).
        """
        repo = model.products()
        conn = model._conn # Доступ к соединению для проверки
    
        # 1. Подготовка: Добавляем ингредиенты
        model.ingredients().add('Мука', 'кг')
    
        # 2. Добавление продукта с рецептом
        recipe = [{'name': 'Мука', 'quantity': 1.0}]
        repo.add(name='Пирог', price=500, ingredients=recipe)
    
        # Проверка: В таблице recipes должна быть 1 запись
        initial_recipe_count = conn.execute("SELECT COUNT(*) FROM product_ingredients").fetchone()[0]
        assert initial_recipe_count == 1
    
        # 3. Действие: Удаление продукта
        repo.delete('Пирог')
        assert repo.has('Пирог') is False
    
        # 4. Проверка: В таблице recipes должно быть 0 записей (Каскадное удаление сработало)
        final_recipe_count = conn.execute("SELECT COUNT(*) FROM product_ingredients").fetchone()[0]
        assert final_recipe_count == 0

    def test_data(self, model: SQLiteModel):
        repo = model.products()
        
        # Для добавления продукта нужны ингредиенты
        model.ingredients().add('Инг1', 'кг')
        
        repo.add(name='Торт', price=1000, ingredients=[{'name': 'Инг1', 'quantity': 1.0}])
        repo.add(name='Кекс', price=50, ingredients=[])
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Торт'
        assert data[1].price == 50
        assert len(data[0].ingredients) == 1 # Проверка, что рецепт загрузился

# --- 5. Тесты для ExpensesRepository ---

class TestExpensesRepository:

    def test_add_expense(self, model: SQLiteModel):
        repo = model.expenses()
        
        # Создаем тип расхода для теста
        model.expense_types().add(name='Свет', default_price=1000, category_name='Платежи')
        
        repo.add(name='Свет', price=1200, quantity=1.0, supplier_name = None)
        
        assert repo.len() == 1
        expense = repo.data()[0]
        assert expense.name == 'Свет'
        assert expense.price == 1200
        assert expense.quantity == 1.0
        
    def test_add_expense_invalid_type(self, model: SQLiteModel):
        repo = model.expenses()
        
        with pytest.raises(ValueError, match="Тип расхода 'Неизвестно' не найден."):
            repo.add(name='Неизвестно', price=100, quantity=1.0, supplier_name=None)
    
    def test_data(self, model: SQLiteModel):
        repo = model.expenses()
        # Создаем тип расхода (Мука)
        model.expense_types().add(name='Мука', default_price=100, category_name='Сырьё')
        
        repo.add(name='Мука', price=150, quantity=10.0, supplier_name=None)
        
        data = repo.data()
        assert len(data) == 1
        assert data[0].name == 'Мука'
        assert data[0].price == 150
        assert data[0].quantity == 10.0

    def test_add_expense_with_supplier(self, expense_data: dict):
        """Проверяет корректное добавление расхода, привязанного к поставщику."""
        model = expense_data['model']
        e_repo = model.expenses()
        
        # Данные уже созданы в фикстуре expense_data:
        # Расход "Мука" (привязан к "Мукомольный завод №1")
        expenses = e_repo.data()
        
        # Находим расход с мукой
        flour_expense = next(e for e in expenses if e.name == "Мука")
        
        # Получаем ID поставщика
        supplier_id = model.suppliers().by_name("Мукомольный завод №1").id
        
        # Проверка привязки
        assert flour_expense.supplier_id == supplier_id
        
        # Находим расход без поставщика
        rent_expense = next(e for e in expenses if e.name == "Аренда")
        assert rent_expense.supplier_id is None
        
    def test_add_expense_nonexistent_supplier_raises_error(self, expense_data: dict):
        """Проверяет, что при попытке привязать расход к несуществующему поставщику, 
        происходит откат и вызывается ошибка."""
        model = expense_data['model']
        e_repo = model.expenses()
        original_len = e_repo.len()
        
        with pytest.raises(ValueError) as excinfo:
            e_repo.add("Мука", 50, 5.0, supplier_name="Несуществующий Поставщик")
            
        assert "Поставщик 'Несуществующий Поставщик' не найден" in str(excinfo.value)
        # Проверяем, что расход не был добавлен
        assert e_repo.len() == original_len

# --- 6. Тесты для SalesRepository (Сложная логика списания) ---

class TestSalesRepository:

    @pytest.fixture(autouse=True)
    def setup_stock_and_products(self, model: SQLiteModel):
        # 1. Зависимости
        model.ingredients().add('Мука', 'кг')
        model.stock().update('Мука', 10.0) # Запас: 10 кг
        
        # 2. Продукт: 1 Булочка = 0.5 кг Муки
        recipe = [{'name': 'Мука', 'quantity': 0.5}]
        model.products().add(name='Булочка', price=80, ingredients=recipe)
        
    def test_add_sale_and_stock_deduction(self, model: SQLiteModel):
        repo = model.sales()
        initial_stock = model.stock().get('Мука').quantity # 10.0
        
        # Продажа 4-х Булочек. Списание: 4 * 0.5 кг = 2.0 кг
        repo.add(name='Булочка', price=80, quantity=4.0, discount=10) 
        
        final_stock = model.stock().get('Мука').quantity # 10.0 - 2.0 = 8.0
        
        assert repo.len() == 1
        sale = repo.data()[0]
        assert sale.product_name == 'Булочка'
        assert sale.quantity == 4.0
        assert final_stock == 8.0
        
    def test_sale_denied_insufficient_stock(self, model: SQLiteModel):
        repo = model.sales()
        # Попытка продать 30 Булочек. Списание: 30 * 0.5 кг = 15.0 кг (есть 10.0 кг)
        
        with pytest.raises(ValueError, match=r"Недостаточно запаса для 'Мука'. Требуется списание 15.00, текущий остаток 10.00."):
            repo.add(name='Булочка', price=80, quantity=30.0, discount=0)
            
        # Проверка, что транзакция была откатана
        assert model.sales().empty() is True
        assert model.stock().get('Мука').quantity == 10.0 # Запасы не должны измениться
    
    def test_data(self, model: SQLiteModel):
        repo = model.sales()
        # Используем продукт, созданный в setup_stock_and_products
        
        repo.add(name='Булочка', price=80, quantity=1.0, discount=0) 
        repo.add(name='Булочка', price=80, quantity=2.0, discount=10) 
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].quantity == 1.0
        assert data[1].discount == 10
        assert data[1].product_name == 'Булочка'

# --- 7. Тесты для UtilsRepository (Справочники) ---

class TestUtilsRepository:

    @pytest.fixture
    def repo(self, conn: sqlite3.Connection) -> UtilsRepository:
        """Предоставляет чистый репозиторий для справочников."""
        return UtilsRepository(conn)

    def test_get_unit_names(self, repo: UtilsRepository):
        """Проверяет, что список единиц измерения корректно извлекается."""
        names = repo.get_unit_names()
        
        # Ожидаемые имена из model/database.py: INITIAL_UNITS
        expected_names = ['кг', 'грамм', 'литр', 'штук']
        
        assert len(names) == len(expected_names)
        assert names == expected_names
        
    def test_get_stock_category_names(self, repo: UtilsRepository):
        """Проверяет, что список категорий запасов корректно извлекается."""
        names = repo.get_stock_category_names()
        
        # Ожидаемые имена из model/database.py: INITIAL_STOCK_CATEGORIES
        expected_names = ['Сырье', 'Упаковка', 'Оборудование']
        
        assert len(names) == len(expected_names)
        assert names == expected_names

    def test_get_expense_category_names(self, repo: UtilsRepository):
        """Проверяет, что список категорий расходов корректно извлекается."""
        names = repo.get_expense_category_names()
        
        # Ожидаемые имена из model/database.py: INITIAL_EXPENSE_CATEGORIES
        expected_names = ['Сырьё', 'Оборудование', 'Платежи', 'Другое']
        
        assert len(names) == len(expected_names)
        assert names == expected_names

    def test_order_of_names(self, repo: UtilsRepository, conn: sqlite3.Connection):
        """Проверяет, что порядок возвращаемых имен соответствует порядку добавления (по ID)."""
        # Вставляем тестовую единицу измерения, которая по алфавиту была бы первой, 
        # но по ID будет последней
        conn.execute("INSERT INTO units (name) VALUES (?)", ('тест_ААА',))
        conn.commit()
        
        names = repo.get_unit_names()
        
        # Ожидаемый порядок: 'кг', 'грамм', 'литр', 'штук', 'тест_ААА'
        # Если бы не было ORDER BY id, 'тест_ААА' была бы где-то в середине.
        assert names[-1] == 'тест_ААА'

    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: sqlite3.Connection):
        """Проверяет успешное получение ID для известной категории."""
               
        # Мы знаем, что 'Сырьё' (INGREDIENT) должна быть в БД после инициализации
        ingredient_id = repo.get_expense_category_id_by_name('Сырьё')
        
        # ID категории должны быть > 0
        assert isinstance(ingredient_id, int)
        assert ingredient_id >= 1 

    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: sqlite3.Connection):
        """Проверяет, что возвращается None для несуществующей категории."""
        
        unknown_id = repo.get_expense_category_id_by_name('Реклама')
        
        assert unknown_id is None
        
    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: sqlite3.Connection):
        """Проверяет, что поиск чувствителен к регистру (по умолчанию в SQLite)."""
        
        # Если в базе 'Сырьё', то 'сырьё' должно вернуть None
        lowercase_id = repo.get_expense_category_id_by_name('сырьё')
        
        # Примечание: В SQLite по умолчанию сравнение строк без учета регистра, 
        # но для русских букв может работать как чувствительное, 
        # поэтому мы просто проверяем, что оно корректно находит точное имя.
        assert lowercase_id is None
        
        # Если очень хочется убедиться, что 'Сырьё' существует:
        assert repo.get_expense_category_id_by_name('Сырьё') is not None

class TestWriteOffsRepository:
    
    # =================================================================
    # ТЕСТЫ НА УСПЕШНОЕ СПИСАНИЕ
    # =================================================================

    def test_add_write_off_product_success(self, write_off_data: dict):
        """Проверяет успешное списание готового продукта (УМЕНЬШАЕТ Stock ингредиентов)."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        flour_name = write_off_data['flour_name']
        croissant_name = write_off_data['croissant_name']
        
        initial_flour_stock = model.stock().get(flour_name).quantity # 10.0 кг
        write_off_qty = 5.0 # Списываем 5 круассанов
        
        # Ожидаемое списание: 5 * 0.1 кг = 0.5 кг муки
        expected_flour_decrease = write_off_qty * 0.1 
        
        w_repo.add(
            item_name=croissant_name,
            item_type="product",
            quantity=write_off_qty,
            reason="Просрочка"
        )
        
        # 1. Проверяем, что запас МУКИ уменьшился
        final_flour_stock = model.stock().get(flour_name).quantity
        assert final_flour_stock == initial_flour_stock - expected_flour_decrease
        assert final_flour_stock == 9.5
        
        # 2. Проверяем, что запись о списании продукта создана
        assert w_repo.len() == 1
        write_off_record = w_repo.data()[0]
        assert write_off_record.product_id == write_off_data['croissant_id']
        assert write_off_record.stock_item_id is None # Списывается продукт, а не StockItem
        assert write_off_record.quantity == write_off_qty

    def test_add_write_off_stock_success(self, write_off_data: dict):
        """Проверяет успешное списание сырья (уменьшение Stock)."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        flour_name = write_off_data['flour_name']
        initial_stock = model.stock().get(flour_name).quantity # 10.0
        write_off_qty = 2.5 
        
        w_repo.add(
            item_name=flour_name,
            item_type="stock",
            quantity=write_off_qty,
            reason="Испорчено влагой"
        )
        
        # 1. Проверяем, что запас уменьшился
        final_stock = model.stock().get(flour_name).quantity
        assert final_stock == initial_stock - write_off_qty
        
        # 2. Проверяем, что запись о списании создана (product_id должен быть None)
        assert w_repo.len() == 1
        write_off_record = w_repo.data()[0]
        assert write_off_record.product_id is None
        # Проверяем, что stock_item_id ЗАПОЛНЕН для сырья
        assert write_off_record.stock_item_id == model.stock().get(flour_name).id
        assert write_off_record.quantity == write_off_qty

    # =================================================================
    # ТЕСТЫ НА ОШИБКИ СПИСАНИЯ
    # =================================================================
    
    def test_write_off_insufficient_product_stock(self, write_off_data: dict):
        """
        Проверяет ошибку при попытке списать продукт, на производство которого
        не хватает ингредиентов.
        """
        model = write_off_data['model']
        w_repo = model.writeoffs()
        flour_name = write_off_data['flour_name']
        
        # Текущий запас муки: 10.0 кг. Рецепт: 0.1 кг/шт.
        # Для 101 круассана нужно 101 * 0.1 = 10.1 кг.
        write_off_qty = 101.0 
        
        initial_stock = model.stock().get(flour_name).quantity 

        # Ожидаем ошибку ValueError
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=write_off_data['croissant_name'],
                item_type="product",
                quantity=write_off_qty,
                reason="Тест нехватки продукта"
            )
        
        # Проверяем, что запас НЕ изменился (откат транзакции)
        final_stock = model.stock().get(flour_name).quantity
        assert final_stock == initial_stock
        
        # Проверяем, что запись о списании НЕ создана
        assert w_repo.len() == 0
        assert "Не хватает ингредиента" in str(excinfo.value)
        
    
    def test_write_off_insufficient_stock(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать больше сырья, чем есть на складе."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        flour_name = write_off_data['flour_name']
        
        initial_stock = model.stock().get(flour_name).quantity # 10.0
        write_off_qty = 15.0 
        
        # Ожидаем ошибку ValueError
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=flour_name,
                item_type="stock",
                quantity=write_off_qty,
                reason="Нехватка сырья"
            )
        
        # Проверяем, что запас не изменился (откат транзакции)
        final_stock = model.stock().get(flour_name).quantity
        assert final_stock == initial_stock
        
        # Проверяем, что запись о списании НЕ создана
        assert w_repo.len() == 0
        assert "Недостаточно запаса" in str(excinfo.value)


    def test_write_off_non_existent_item_product(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать несуществующий продукт."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name="Торт Наполеон",
                item_type="product",
                quantity=1.0,
                reason="Ошибка инвентаризации"
            )
        
        assert w_repo.len() == 0
        assert "не найден в списке продуктов" in str(excinfo.value)
        
    def test_write_off_non_existent_item_stock(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать несуществующее сырье/запас."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name="Новый Ингредиент",
                item_type="stock",
                quantity=1.0,
                reason="Ошибка инвентаризации"
            )
        
        assert w_repo.len() == 0
        assert "не найден на складе для списания" in str(excinfo.value)


    def test_write_off_invalid_item_type(self, write_off_data: dict):
        """Проверяет ошибку при недопустимом типе элемента."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=write_off_data['flour_name'],
                item_type="equipment", # Недопустимый тип
                quantity=1.0,
                reason="Тест"
            )
        
        assert w_repo.len() == 0
        assert "Недопустимый тип элемента" in str(excinfo.value)

    def test_write_off_non_positive_quantity(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать нулевое или отрицательное количество."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=write_off_data['croissant_name'],
                item_type="product",
                quantity=0.0,
                reason="Тест"
            )
        
        assert w_repo.len() == 0
        assert "Количество для списания должно быть положительным" in str(excinfo.value)
        
    # =================================================================
    # ТЕСТЫ НА МЕТОДЫ ПОЛУЧЕНИЯ ДАННЫХ
    # =================================================================

    def test_data_and_len(self, write_off_data: dict):
        """Проверяет получение списка списаний и их количества."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        # Списание продукта (уменьшает ингредиенты, регистрирует продукт)
        w_repo.add("Круассан", "product", 2.0, "Тест 2")
        # Списание сырья (уменьшает сырье, регистрирует сырье)

        #time.sleep(6)

        w_repo.add("Мука", "stock", 1.0, "Тест 1")

        assert w_repo.len() == 2
        
        all_write_offs = w_repo.data()
        assert len(all_write_offs) == 2
        
        # Проверяем, что первый элемент (самый новый, т.к. ORDER BY date DESC) - это Мука
        assert all_write_offs[1].quantity == 1.0
        assert all_write_offs[1].product_id is None # Мука - сырье, product_id пуст
        
        # Проверяем, что второй элемент - это Круассан
        assert all_write_offs[0].quantity == 2.0
        assert all_write_offs[0].product_id == write_off_data['croissant_id'] # Круассан - продукт, product_id заполнен

class TestSuppliersRepository:
    """Тесты для репозитория SuppliersRepository."""

    def test_add_supplier(self, model: SQLiteModel):
        """Проверяет корректное добавление нового поставщика."""
        repo = model.suppliers()
        
        # Добавляем нового поставщика с полными данными
        supplier = repo.add(
            name="Пекарское Оборудование", 
            contact_person="Анна Смирнова", 
            phone="89101112233", 
            email="anna@equipment.com", 
            address="г. Москва, ул. Пекарская, 5"
        )
        
        assert supplier.id is not None
        assert supplier.name == "Пекарское Оборудование"
        assert supplier.contact_person == "Анна Смирнова"
        assert supplier.phone == "89101112233"
        assert supplier.email == "anna@equipment.com"
        assert supplier.address == "г. Москва, ул. Пекарская, 5"
        assert repo.len() == 1

    def test_add_duplicate_supplier_raises_error(self, model: SQLiteModel):
        """Проверяет, что добавление поставщика с существующим именем вызывает ошибку."""
        repo = model.suppliers()
        repo.add("Тестовый Поставщик", phone="1")
        
        with pytest.raises(ValueError) as excinfo:
            repo.add("Тестовый Поставщик", phone="2") # Повтор
            
        assert "уже существует" in str(excinfo.value)
        assert repo.len() == 1 # Проверяем, что дубликат не был добавлен

    def test_get_by_id_and_by_name(self, model: SQLiteModel):
        """Проверяет получение поставщика по ID и по имени."""
        repo = model.suppliers()
        
        # Добавляем поставщика и запоминаем ID
        supplier_added = repo.add("Молокозавод 'Свежий'", "Олег")
        
        # Получение по ID
        supplier_by_id = repo.get(supplier_added.id)
        assert supplier_by_id is not None
        assert supplier_by_id.name == "Молокозавод 'Свежий'"
        
        # Получение по имени
        supplier_by_name = repo.by_name("Молокозавод 'Свежий'")
        assert supplier_by_name is not None
        assert supplier_by_name.id == supplier_added.id
        
        # Тест на несуществующего
        assert repo.get(999) is None
        assert repo.by_name("Несуществующий") is None

    def test_data_and_names(self, model: SQLiteModel):
        """Проверяет получение списка всех поставщиков и списка только их имен."""
        repo = model.suppliers()
        
        repo.add("Поставщик A", "A")
        repo.add("Поставщик B", "B")
        repo.add("Поставщик C", "C")
        
        # Проверка data()
        all_suppliers = repo.data()
        assert len(all_suppliers) == 3
        # Проверяем сортировку по имени
        assert all_suppliers[0].name == "Поставщик A"
        
        # Проверка names()
        all_names = repo.names()
        assert all_names == ["Поставщик A", "Поставщик B", "Поставщик C"]
        
    def test_delete_supplier(self, model: SQLiteModel):
        """Проверяет удаление поставщика по имени."""
        repo = model.suppliers()
        repo.add("Удаляемый Поставщик")
        repo.add("Остающийся Поставщик")
        
        assert repo.len() == 2
        
        # Удаляем
        repo.delete("Удаляемый Поставщик")
        
        assert repo.len() == 1
        assert repo.by_name("Удаляемый Поставщик") is None
        assert repo.by_name("Остающийся Поставщик") is not None
        
        # Удаление несуществующего не вызывает ошибку
        repo.delete("Несуществующий")
        assert repo.len() == 1

    def test_update_all_fields(self, supplier_data: dict):
        """Проверяет успешное обновление всех полей поставщика."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id1']
        
        # Обновляем все поля
        updated_supplier = s_repo.update(
            supplier_id=supplier_id,
            name="Новая Мука",
            contact_person="Сидоров С.С.",
            phone="999-0001",
            email="sidorov@new.com",
            address="ул. Обновленная, 10"
        )
        
        # Проверяем, что объект обновлен
        assert updated_supplier.name == "Новая Мука"
        assert updated_supplier.contact_person == "Сидоров С.С."
        assert updated_supplier.phone == "999-0001"
        assert updated_supplier.email == "sidorov@new.com"
        assert updated_supplier.address == "ул. Обновленная, 10"
        
        # Проверяем, что данные в БД корректны
        db_supplier = s_repo.get(supplier_id)
        assert db_supplier.name == "Новая Мука"


    def test_update_only_name(self, supplier_data: dict):
        """Проверяет обновление только имени, остальные поля должны сохраниться/обнулиться."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id2'] # ID поставщика "Дрожжи и Добавки"
        
        # --- ИСПРАВЛЕНИЕ: Получаем оригинальный объект для частичного обновления ---
        original_supplier = s_repo.get(supplier_id)
        
        # Обновляем только имя. Для сохранения контактных данных передаем их обратно.
        updated_supplier = s_repo.update(
            supplier_id=supplier_id,
            name="Новые Дрожжи",
            # Передаем оригинальные значения, чтобы они не были обнулены
            contact_person=original_supplier.contact_person, 
            phone=original_supplier.phone,
            email=original_supplier.email,
            address=original_supplier.address
        )
        
        assert updated_supplier.name == "Новые Дрожжи"
        # Проверка, что оригинальное значение сохранилось
        assert updated_supplier.contact_person == "Петров П.П." 
        assert updated_supplier.phone is None 
        assert updated_supplier.email is None 
        assert updated_supplier.address is None
        
    def test_update_non_existent_supplier(self, supplier_data: dict):
        """Проверяет ошибку при попытке обновить несуществующий ID."""
        s_repo = supplier_data['repo']
        
        with pytest.raises(ValueError) as excinfo:
            s_repo.update(
                supplier_id=99999,
                name="Фантомный поставщик"
            )
        
        assert "Поставщик с ID 99999 не найден" in str(excinfo.value)

    def test_update_duplicate_name(self, supplier_data: dict):
        """Проверяет ошибку IntegrityError при попытке установить дублирующееся имя."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id2'] # ID "Дрожжи и Добавки"
        
        # Пытаемся переименовать в имя первого поставщика
        with pytest.raises(ValueError) as excinfo:
            s_repo.update(
                supplier_id=supplier_id,
                name="Мука и Зерно" # Имя уже занято
            )
        
        assert "Поставщик с именем 'Мука и Зерно' уже существует" in str(excinfo.value)
        
    def test_delete_used_supplier(self, supplier_data: dict, model: SQLiteModel):
        """Проверяет ошибку при попытке удалить поставщика, связанного с расходами."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id1'] # ID поставщика "Мука и Зерно"
        supplier_name = "Мука и Зерно"

        # 1. Добавляем тип расхода (например, "Закупка муки")
        # Для простоты, ExpenseType не привязывается напрямую к Supplier,
        # поэтому мы сразу создаем расход.
        
        # NOTE: В ExpensesRepository.add() нет параметра supplier_id,
        # поэтому для теста мы должны выполнить прямой SQL запрос,
        # чтобы связать расход с поставщиком. 
        # Если вы хотите использовать add(), нужно его изменить.
        
        # Создаем тип расхода для использования
        model.expense_types().add(
            name="Закупка сырья у поставщика", 
            default_price=1000, 
            category_name="Сырьё"
        )
        
        # Регистрируем расход, привязанный к поставщику
        # Если бы ExpensesRepository.add() имел supplier_id, мы бы использовали его.
        # Поскольку его нет, используем прямой SQL для имитации связи:
        
        expense_type_id = model.expense_types().get("Закупка сырья у поставщика").id

        cursor = model._conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (type_id, name, price, category_id, quantity, date, supplier_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (expense_type_id, "Расход", 1000, 1, 10.0, "2025-10-01 10:00", supplier_id)
        )
        model._conn.commit()

        # 2. Пытаемся удалить поставщика
        with pytest.raises(ValueError) as excinfo:
            s_repo.delete(supplier_name)
        
        assert f"Поставщик '{supplier_name}' связан с существующими расходами. Удаление невозможно." in str(excinfo.value)
        
        # Проверяем, что поставщик остался
        assert s_repo.by_name(supplier_name) is not None