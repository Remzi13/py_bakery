# tests/test_products.py

from model.products import Products
from unittest.mock import Mock, call
import pytest

@pytest.fixture
def mock_ingredients():
    """Мок-объект для Ingredients."""
    m = Mock()
    # Добавляем мок для by_name, который используется в save_to_xml
    mock_ing = Mock(id='12345')
    m.by_name.return_value = mock_ing
    return m

@pytest.fixture
def products(mock_ingredients):
    """Фикстура для Products с добавленными продуктами."""
    prod = Products(mock_ingredients)
    prod.add("Круассан", 150, [{'name': 'Мука', 'quantity': 0.1}, {'name': 'Яйца', 'quantity': 1}])
    prod.add("Багет", 80, [{'name': 'Мука', 'quantity': 0.5}])
    return prod

def test_products_add(products):
    """Проверяем добавление продукта."""
    assert products.len() == 2
    assert products.by_name("Круассан") is not None

def test_products_update(products):
    """Проверяем обновление существующего продукта."""
    new_ingredients = [{'name': 'Мука', 'quantity': 0.2}]
    products.add("Круассан", 180, new_ingredients) # Обновление
    
    kr = products.by_name("Круассан")
    assert kr.price == 180
    assert kr.ingredients == new_ingredients
    assert products.len() == 2 # Количество не должно измениться

def test_products_by_name(products):
    """Проверяем получение продукта по имени."""
    assert products.by_name("Багет").price == 80
    assert products.by_name("Пирожок") is None

def test_products_delete(products):
    """Проверяем удаление продукта."""
    products.delete("Круассан")
    assert products.by_name("Круассан") is None
    assert products.len() == 1
    
    products.delete("Несуществующий") # Должно пройти без ошибок
    assert products.len() == 1