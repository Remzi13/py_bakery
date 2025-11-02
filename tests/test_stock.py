# tests/test_stock.py

from model.stock import Stock
from model.entities import StockCategory, Unit
import pytest

@pytest.fixture
def empty_stock():
    """Фикстура для создания пустого объекта Stock."""
    return Stock()

@pytest.fixture
def populated_stock(empty_stock):
    """Фикстура для Stock с добавленными элементами."""
    empty_stock.add("Мука", StockCategory.INGREDIENT, 10.0, Unit.Kilogram)
    empty_stock.add("Молоко", StockCategory.INGREDIENT, 5.0, Unit.Liter)
    return empty_stock

def test_stock_add_and_get(populated_stock):
    """Проверяем добавление и получение элемента по имени."""
    item = populated_stock.get("Мука")
    assert item is not None
    assert item.name == "Мука"
    assert item.quantity == 10.0
    assert populated_stock.len() == 2

def test_stock_set_quantity(populated_stock):
    """Проверяем установку нового количества."""
    populated_stock.set("Мука", 50.0)
    assert populated_stock.get("Мука").quantity == 50.0

def test_stock_set_non_existent(empty_stock):
    """Проверяем исключение при попытке установить количество несуществующего элемента."""
    with pytest.raises(KeyError, match="Элемент 'Сахар' не найден в инвентаре"):
        empty_stock.set("Сахар", 10.0)

def test_stock_update_quantity(populated_stock):
    """Проверяем обновление (добавление/вычитание) количества."""
    populated_stock.update("Мука", -2.0)
    assert populated_stock.get("Мука").quantity == 8.0
    
    populated_stock.update("Молоко", 10.0)
    assert populated_stock.get("Молоко").quantity == 15.0

def test_stock_update_non_existent(empty_stock):
    """Проверяем исключение при попытке обновить количество несуществующего элемента."""
    with pytest.raises(KeyError, match="Элемент 'Сахар' не найден в инвентаре"):
        empty_stock.update("Сахар", 5.0)

def test_stock_delete(populated_stock):
    """Проверяем удаление элемента."""
    populated_stock.delete("Мука")
    assert populated_stock.get("Мука") is None
    assert populated_stock.len() == 1
    assert populated_stock.get("Молоко") is not None