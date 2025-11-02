# tests/test_expense_types_expenses.py

from model.expenses import ExpenseTypes, Expenses
from model.entities import ExpenseCategory
import pytest

@pytest.fixture
def expense_types():
    """Фикстура для ExpenseTypes с добавленными типами."""
    types = ExpenseTypes()
    types.add("Мука", 100, ExpenseCategory.INGREDIENT)
    types.add("Аренда", 50000, ExpenseCategory.PAYMENT)
    return types

@pytest.fixture
def expenses(expense_types):
    """Фикстура для Expenses с добавленными расходами."""
    exp = Expenses(expense_types)
    exp.add("Мука", 120, 10) # 120 * 10 = 1200
    exp.add("Аренда", 50000, 1) # 50000 * 1 = 50000
    return exp

# --- Тесты для ExpenseTypes ---

def test_expense_types_add_and_get(expense_types):
    """Проверяем добавление и получение типа расхода."""
    etype = expense_types.get("Мука")
    assert etype is not None
    assert etype.default_price == 100
    assert expense_types.len() == 2

def test_expense_types_delete(expense_types):
    """Проверяем удаление типа расхода."""
    expense_types.delete("Мука")
    assert expense_types.get("Мука") is None
    assert expense_types.len() == 1

# --- Тесты для Expenses ---

def test_expenses_add(expenses):
    """Проверяем добавление фактического расхода."""
    assert expenses.len() == 2
    
def test_expenses_add_non_existent_type(expense_types):
    """Проверяем исключение при добавлении расхода с несуществующим типом."""
    exp = Expenses(expense_types)
    with pytest.raises(ValueError, match="Тип расхода 'Упаковка' не найден"):
        exp.add("Упаковка", 10, 100)