# tests/test_ingredients.py

from model.ingredients import Ingredients
from model.entities import Unit, ExpenseCategory
from unittest.mock import Mock, call
import pytest

# Фикстура для мок-объекта Model, имитирующая его методы
@pytest.fixture
def mock_model():
    m = Mock()
    # Настройка мока для ExpenseTypes, который используется при добавлении
    m.expense_types.return_value = Mock()
    m.products.return_value = Mock()
    return m

@pytest.fixture
def ingredients(mock_model):
    """Фикстура для Ingredients с добавленным ингредиентом."""
    ing = Ingredients(mock_model)
    ing.add("Мука", Unit.Kilogram)
    ing.add("Яйца", Unit.Piece)
    return ing

def test_ingredients_add(ingredients, mock_model):
    """Проверяем добавление ингредиента и вызовы методов Model."""
    assert ingredients.len() == 2
    assert ingredients.by_name("Мука") is not None
    
    # Проверка, что были вызваны методы Model для Stock и ExpenseTypes
    # 'Мука' и 'Яйца'
    assert mock_model.add_stock_item.call_count == 2
    mock_model.add_stock_item.assert_has_calls([
        call("Мука", 0, 0, unit=Unit.Kilogram),
        call("Яйца", 0, 0, unit=Unit.Piece),
    ], any_order=True)

    # Проверка вызова добавления типа расхода
    assert mock_model.expense_types.return_value.add.call_count == 2
    mock_model.expense_types.return_value.add.assert_has_calls([
        call("Мука", 100, ExpenseCategory.INGREDIENT),
        call("Яйца", 100, ExpenseCategory.INGREDIENT),
    ], any_order=True)


def test_ingredients_can_delete_true(ingredients, mock_model):
    """Проверяем возможность удаления, если ингредиент не используется."""
    # Убеждаемся, что products().data() возвращает пустой список или продукт без этого ингредиента
    mock_model.products.return_value.data.return_value = [] 
    assert ingredients.can_delete("Мука") == True

def test_ingredients_can_delete_false(ingredients, mock_model):
    """Проверяем невозможность удаления, если ингредиент используется в продукте."""
    # Имитация продукта, который использует "Мука"
    mock_product = Mock()
    mock_product.ingredients = [{'name': 'Мука', 'quantity': 10}]
    mock_model.products.return_value.data.return_value = [mock_product] 
    
    assert ingredients.can_delete("Мука") == False

def test_ingredients_delete_success(ingredients, mock_model):
    """Проверяем успешное удаление ингредиента и вызовы методов Model."""
    # Убеждаемся, что can_delete() будет True
    ingredients.can_delete = Mock(return_value=True) 

    ingredients.delete("Мука")
    assert ingredients.by_name("Мука") is None
    assert ingredients.len() == 1

    # Проверка, что были вызваны методы Model для удаления
    mock_model.delete_stock_item.assert_called_once_with("Мука")
    mock_model.expense_types.return_value.delete.assert_called_once_with("Мука")

def test_ingredients_delete_failure(ingredients, mock_model):
    """Проверяем исключение при попытке удалить используемый ингредиент."""
    # Убеждаемся, что can_delete() будет False
    ingredients.can_delete = Mock(return_value=False) 

    with pytest.raises(ValueError):
        ingredients.delete("Мука")
    
    assert ingredients.by_name("Мука") is not None