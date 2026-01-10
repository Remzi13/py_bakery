import pytest

from tests.core import conn, get_unit_by_name, sqlite3, SQLiteModel, TEST_DB, model

@pytest.fixture
def expense_data(model: SQLiteModel) -> dict:
    """Подготавливает данные для тестов ExpensesRepository."""
    # 1. Создаем поставщиков (НОВЫЙ ШАГ)
    supplier_repo = model.suppliers()
    supplier_repo.add("Мукомольный завод №1", "Иван Иванов", "+71234567890", "ivan@mill.ru", "ул. Мельничная, 1")
    supplier_repo.add("ООО 'Packaging'", "Петр Петров", "88001234567")
    
    # 2. Создаем типы расходов (Materials и Платежи)
    model.expense_types().add("Мука пшеничная", 50, "Materials")
    model.expense_types().add("Аренда", 50000, "Utilities")
    
    # 3. Добавляем ингредиент (он автоматически создаст StockItem и ExpenseType)
    # This is important so that ExpenseTypesRepository can find "Мука пшеничная"
    model.stock().add("Мука", "Materials", 50, "kg")
    
    # 4. Добавляем несколько расходов
    # Расход, связанный с поставщиком
    model.expenses().add("Мука", 45, 100.0, supplier_name="Мукомольный завод №1")
    # Расход без поставщика
    model.expenses().add("Аренда", 50000, 1.0, supplier_name=None)
    
    # 5. Возвращаем данные для теста
    return {
        'model': model
    }

class TestExpensesRepository:

    def test_add_expense(self, model: SQLiteModel):
        repo = model.expenses()
        
        # Создаем тип расхода для теста
        model.expense_types().add(name='Свет', default_price=1000, category_name='Utilities')
        
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
        model.expense_types().add(name='Мука', default_price=100, category_name='Materials')
        
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
