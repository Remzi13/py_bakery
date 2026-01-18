import pytest
from sqlalchemy.orm import Session

from tests.core import conn

from repositories.utils import UtilsRepository
from sql_model.entities import Unit

class TestUtilsRepository:

    @pytest.fixture
    def repo(self, conn: Session) -> UtilsRepository:
        """Provides a clean repository for reference data."""
        return UtilsRepository(conn)

    def test_get_unit_names(self, repo: UtilsRepository):
        """Checks that the list of units is correctly retrieved."""
        names = repo.get_unit_names()
        
        # Expected names from database.py: default_units
        expected_names = ['kg', 'g', 'l', 'pc']
        
        assert len(names) == len(expected_names)
        assert names == expected_names
        
    def test_get_stock_category_names(self, repo: UtilsRepository):
        """Checks that the list of stock categories is correctly retrieved."""
        names = repo.get_stock_category_names()
        
        # Expected names from database.py: default_stock_categories
        expected_names = ['Materials', 'Packaging', 'Equipment']
        
        assert len(names) == len(expected_names)
        assert names == expected_names

    def test_get_expense_category_names(self, repo: UtilsRepository):
        """Checks that the list of expense categories is correctly retrieved."""
        names = repo.get_expense_category_names()
        
        # Expected names from database.py: default_expense_categories
        expected_names = ['Materials', 'Equipment', 'Utilities', 'Other']
        
        assert len(names) == len(expected_names)
        assert names == expected_names

    def test_order_of_names(self, repo: UtilsRepository, conn: Session):
        """Checks that the order of returned names matches the order of addition (by ID)."""
        # Add a test unit that would be first alphabetically but last by ID
        conn.add(Unit(name='тест_ААА'))
        conn.commit()
        
        names = repo.get_unit_names()
        
        # Ожидаемый порядок: 'kg', 'g', 'l', 'pc', 'тест_ААА'
        # Если бы не было ORDER BY id, 'тест_ААА' была бы где-то в середине.
        assert names[-1] == 'тест_ААА'

    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: Session):
        """Проверяет успешное получение ID для известной категории."""
               
        # Мы знаем, что 'Materials' (MATERIAL) должна быть в БД после инициализации
        mat_id = repo.get_expense_category_id_by_name('Materials')
        
        # ID категории должны быть > 0
        assert isinstance(mat_id, int)
        assert mat_id >= 1 

    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: Session):
        """Проверяет, что возвращается None для несуществующей категории."""
        
        unknown_id = repo.get_expense_category_id_by_name('Реклама')    
        
        assert unknown_id is None
        
    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: Session):
        """Проверяет, что поиск чувствителен к регистру (по умолчанию в SQLite)."""
        
        # Если в базе 'Materials', то 'Materials' должно вернуть None
        lowercase_id = repo.get_expense_category_id_by_name('materials')
        
        # Примечание: В SQLite по умолчанию сравнение строк без учета регистра, 
        # но для русских букв может работать как чувствительное, 
        # поэтому мы просто проверяем, что оно корректно находит точное имя.
        assert lowercase_id is None
        
        # Если очень хочется убедиться, что 'Materials' существует:
        assert repo.get_expense_category_id_by_name('Materials') is not None
