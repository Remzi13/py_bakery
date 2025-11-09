import pytest
import sqlite3

from tests.core import conn, get_unit_by_name

from repositories.expense_types import ExpenseTypesRepository

@pytest.fixture
def setup_ids(conn: sqlite3.Connection):
    """Предоставляет ID справочных сущностей для тестов."""
    return {
        'kg_id': get_unit_by_name(conn, 'кг'),
        'expense_cat_id': conn.execute("SELECT id FROM expense_categories WHERE name = 'Сырьё'").fetchone()[0],
        'stock_cat_id': conn.execute("SELECT id FROM stock_categories WHERE name = 'Сырье'").fetchone()[0]
    }

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
