import pytest
from sqlalchemy.orm import Session

from tests.core import conn, get_unit_by_name, get_category_id_by_name

from repositories.expense_types import ExpenseTypesRepository
from sql_model.entities import ExpenseCategory

@pytest.fixture
def setup_ids(conn: Session):
    """Provides IDs of reference entities for tests."""
    return {
        'kg_id': get_unit_by_name(conn, 'kg'),
        'expense_cat_id': get_category_id_by_name(conn, ExpenseCategory, 'Materials'),
    }

class TestExpenseTypesRepository:
    
    @pytest.fixture
    def repo(self, conn: Session) -> ExpenseTypesRepository:
        return ExpenseTypesRepository(conn)

    def test_add_and_get(self, repo: ExpenseTypesRepository, setup_ids: dict, conn: Session):
       
        repo.add(name='Аренда', default_price=50000, category_name='Utilities')
        expense_type = repo.get('Аренда')
        
        assert expense_type is not None
        assert expense_type.name == 'Аренда'
        assert expense_type.default_price == 50000
        
        # Get category ID using ORM query
        utilities_cat_id = get_category_id_by_name(conn, ExpenseCategory, 'Utilities')
        assert expense_type.category_id == utilities_cat_id
        assert repo.len() == 1
        
    def test_delete(self, repo: ExpenseTypesRepository):
        repo.add(name='Зарплата', default_price=30000, category_name='Utilities')
        assert repo.len() == 1
        
        repo.delete('Зарплата')
        assert repo.get('Зарплата') is None
        assert repo.empty() is True

    def test_data(self, repo: ExpenseTypesRepository):
        repo.add(name='Аренда', default_price=50000, category_name='Utilities')
        repo.add(name='Свет', default_price=1000, category_name='Utilities')
        
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
        repo.add(name='Аренда', default_price=50000, category_name='Utilities')
        repo.add(name='Электричество', default_price=1000, category_name='Utilities')
        repo.add(name='Мука', default_price=50, category_name='Materials')
        
        # 2. Действие: Запрашиваем типы для категории 'Платежи'
        payment_names = repo.get_names_by_category_name('Utilities')
        
        # Проверка 1: Корректное количество и содержимое
        assert len(payment_names) == 2
        # Проверяем, что имена отсортированы (если мы добавили ORDER BY name в SQL)
        assert payment_names == ['Аренда', 'Электричество'] 
        
        # 3. Действие: Запрашиваем типы для категории 'Сырьё'
        mat_names = repo.get_names_by_category_name('Materials')
        
        # Проверка 2: Корректное содержимое
        assert len(mat_names) == 1
        assert mat_names[0] == 'Мука'
        
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
        repo.add(name='Аренда', default_price=50000, category_name='Utilities')
        repo.add(name='Электричество', default_price=1000, category_name='Utilities')
        repo.add(name='Мука', default_price=50, category_name='Materials')
        
        # 2. Действие: Запрашиваем типы для категории 'Платежи'
        payment_expenses = repo.get_by_category_name('Utilities')
        
        # Проверка 1: Корректное количество и содержимое
        assert len(payment_expenses) == 2
        
        # Проверяем, что вернулись полные объекты и они корректно отфильтрованы
        # (Сортировка по имени: 'Аренда' идет раньше 'Электричество')
        assert payment_expenses[0].name == 'Аренда'
        assert payment_expenses[0].default_price == 50000
        assert payment_expenses[1].name == 'Электричество'
        assert payment_expenses[1].default_price == 1000
        
        # 3. Действие: Запрашиваем типы для категории 'Сырьё'
        mat_expenses = repo.get_by_category_name('Materials')
        
        # Проверка 2: Корректное содержимое
        assert len(mat_expenses) == 1
        assert mat_expenses[0].name == 'Мука'
        
        # 4. Проверка на несуществующую категорию
        unknown_expenses = repo.get_by_category_name('Несуществующая Категория')
        assert len(unknown_expenses) == 0
        assert unknown_expenses == []
