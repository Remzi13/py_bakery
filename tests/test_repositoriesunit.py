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
        with pytest.raises(ValueError, match="Недостаточно запаса 'Масло'"):
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
        
        repo.add(name='Свет', price=1200, quantity=1.0)
        
        assert repo.len() == 1
        expense = repo.data()[0]
        assert expense.name == 'Свет'
        assert expense.price == 1200
        assert expense.quantity == 1.0
        
    def test_add_expense_invalid_type(self, model: SQLiteModel):
        repo = model.expenses()
        
        with pytest.raises(ValueError, match="Тип расхода 'Неизвестно' не найден."):
            repo.add(name='Неизвестно', price=100, quantity=1.0)
    
    def test_data(self, model: SQLiteModel):
        repo = model.expenses()
        # Создаем тип расхода (Мука)
        model.expense_types().add(name='Мука', default_price=100, category_name='Сырьё')
        
        repo.add(name='Мука', price=150, quantity=10.0)
        
        data = repo.data()
        assert len(data) == 1
        assert data[0].name == 'Мука'
        assert data[0].price == 150
        assert data[0].quantity == 10.0

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
        
        with pytest.raises(ValueError, match="Недостаточно запаса 'Мука'"):
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