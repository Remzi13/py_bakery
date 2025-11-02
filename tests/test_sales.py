# tests/test_sales.py

from model.sales import Sales
from unittest.mock import Mock, call
import pytest

@pytest.fixture
def mock_stock():
    """Мок-объект для Stock."""
    return Mock()

@pytest.fixture
def mock_products():
    """Мок-объект для Products, возвращающий тестовый продукт."""
    m = Mock()
    
    # Мок-объект Product
    mock_product = Mock()
    mock_product.id = '999'
    mock_product.ingredients = [
        {'name': 'Мука', 'quantity': 0.1}, 
        {'name': 'Сахар', 'quantity': 0.05}
    ]
    
    m.by_name.return_value = mock_product
    return m

@pytest.fixture
def sales(mock_stock, mock_products):
    """Фикстура для Sales с добавленными продажами."""
    s = Sales(mock_stock, mock_products)
    s.add("Круассан", 150, 2, 10) # 2 штуки
    return s

def test_sales_add_success(sales, mock_stock, mock_products):
    """Проверяем успешное добавление продажи и обновление запасов."""
    assert sales.len() == 1
    
    # Проверка, что update был вызван для каждого ингредиента
    assert mock_stock.update.call_count == 2 
    mock_stock.update.assert_has_calls([
        # 0.1 * 2 = 0.2 (уменьшение)
        call('Мука', -0.2),
        # 0.05 * 2 = 0.1 (уменьшение)
        call('Сахар', -0.1), 
    ], any_order=True)

    # Проверка данных о продаже
    sale_data = sales.data()[0]
    assert sale_data.product_name == "Круассан"
    assert sale_data.quantity == 2
    assert sale_data.price == 150
    assert sale_data.discount == 10

def test_sales_add_product_not_found(mock_stock, mock_products):
    """Проверяем исключение при попытке продать несуществующий продукт."""
    s = Sales(mock_stock, mock_products)
    
    # Настройка мока, чтобы он вернул None, т.е. продукт не найден
    mock_products.by_name.return_value = None
    
    with pytest.raises(ValueError, match="Продукт 'Пирожок' не найден"):
        s.add("Пирожок", 50, 1, 0)
        
    assert s.len() == 0
    mock_stock.update.assert_not_called() # Запасы не должны обновляться