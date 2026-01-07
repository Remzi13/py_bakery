import pytest

from tests.core import sqlite3, conn

from repositories.utils import UtilsRepository

class TestUtilsRepository:

    @pytest.fixture
    def repo(self, conn: sqlite3.Connection) -> UtilsRepository:
        """Предоставляет чистый репозиторий для справочников."""
        return UtilsRepository(conn)

    def test_get_unit_names(self, repo: UtilsRepository):
        """Проверяет, что список единиц измерения корректно извлекается."""
        names = repo.get_unit_names()
        
        # Ожидаемые имена из model/database.py: INITIAL_UNITS
        expected_names = ['kg', 'g', 'l', 'pc']
        
        assert len(names) == len(expected_names)
        assert names == expected_names
        
    def test_get_stock_category_names(self, repo: UtilsRepository):
        """Проверяет, что список категорий запасов корректно извлекается."""
        names = repo.get_stock_category_names()
        
        # Ожидаемые имена из model/database.py: INITIAL_STOCK_CATEGORIES
        expected_names = ['Materials', 'Packaging', 'Equipment']
        
        assert len(names) == len(expected_names)
        assert names == expected_names

    def test_get_expense_category_names(self, repo: UtilsRepository):
        """Проверяет, что список категорий расходов корректно извлекается."""
        names = repo.get_expense_category_names()
        
        # Ожидаемые имена из model/database.py: INITIAL_EXPENSE_CATEGORIES
        expected_names = ['Materials', 'Equipment', 'Utilities', 'Other']
        
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
               
        # Мы знаем, что 'Materials' (INGREDIENT) должна быть в БД после инициализации
        ingredient_id = repo.get_expense_category_id_by_name('Materials')
        
        # ID категории должны быть > 0
        assert isinstance(ingredient_id, int)
        assert ingredient_id >= 1 

    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: sqlite3.Connection):
        """Проверяет, что возвращается None для несуществующей категории."""
        
        unknown_id = repo.get_expense_category_id_by_name('Реклама')
        
        assert unknown_id is None
        
    def test_get_expense_category_id_by_name_success(self, repo: UtilsRepository, conn: sqlite3.Connection):
        """Проверяет, что поиск чувствителен к регистру (по умолчанию в SQLite)."""
        
        # Если в базе 'Materials', то 'Materials' должно вернуть None
        lowercase_id = repo.get_expense_category_id_by_name('materials')
        
        # Примечание: В SQLite по умолчанию сравнение строк без учета регистра, 
        # но для русских букв может работать как чувствительное, 
        # поэтому мы просто проверяем, что оно корректно находит точное имя.
        assert lowercase_id is None
        
        # Если очень хочется убедиться, что 'Materials' существует:
        assert repo.get_expense_category_id_by_name('Materials') is not None
