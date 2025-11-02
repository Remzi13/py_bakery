# tests/test_entities.py

from model.entities import unit_by_name, category_by_name, Unit, ExpenseCategory
import pytest

# Тестирование функции unit_by_name
def test_unit_by_name_success():
    """Проверяет корректное преобразование имени единицы в ее значение."""
    assert unit_by_name('кг') == Unit.Kilogram
    assert unit_by_name('штук') == Unit.Piece

def test_unit_by_name_failure():
    """Проверяет вызов исключения, если единица не найдена."""
    with pytest.raises(ValueError, match="Единица измерения 'тонна' не найдена"):
        unit_by_name('тонна')

# Тестирование функции category_by_name
def test_category_by_name_success():
    """Проверяет корректное преобразование имени категории в ее значение."""
    assert category_by_name('Сырьё') == ExpenseCategory.INGREDIENT
    assert category_by_name('Оборудование') == ExpenseCategory.EQUIPMENT

def test_category_by_name_failure():
    """Проверяет вызов исключения, если категория не найдена."""
    with pytest.raises(ValueError, match="Категория 'Зарплата' не найдена"):
        category_by_name('Зарплата')