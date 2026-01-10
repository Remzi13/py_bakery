import pytest
import sqlite3

from tests.core import SQLiteModel, model, conn
from tests.core import conn, get_unit_by_name, sqlite3, SQLiteModel, TEST_DB

from repositories.stock import StockRepository
class TestStockRepository:
 
    def test_add_and_get(self,  model: SQLiteModel):
        model.stock().add(name='Мешок', category_name='Packaging', quantity=100.0, unit_name='pc')
        item = model.stock().get('Мешок')

        assert model.stock().by_id(item.id).name == item.name
        assert item is not None
        assert item.name == 'Мешок'
        assert item.quantity == 100.0
        assert model.stock().len() == 1
        
    def test_update_quantity(self, model: SQLiteModel):
        model.stock().add(name='Вода', category_name='Materials', quantity=50.0, unit_name='l')

        # Оприходование
        model.stock().update('Вода', 10.0)
        assert model.stock().get('Вода').quantity == 60.0
        
        # Списание
        model.stock().update('Вода', -20.0)
        assert model.stock().get('Вода').quantity == 40.0
        
    def test_update_negative_balance(self, model: SQLiteModel):
        model.stock().add(name='Масло', category_name='Materials', quantity=10.0, unit_name='kg')
        
        # Попытка списать больше, чем есть
        with pytest.raises(ValueError, match="Недостаточно запаса для 'Масло'. Требуется списание 100.00, текущий остаток 10.00."):
            model.stock().update('Масло', -100.0)

    def test_data(self, model: SQLiteModel):
        model.stock().add(name='Мука', category_name='Materials', quantity=100.0, unit_name='kg')
        model.stock().add(name='Яйцо', category_name='Materials', quantity=50.0, unit_name='pc')
        
        data = model.stock().data()
        assert len(data) == 2
        assert data[0].name == 'Мука'
        assert data[1].quantity == 50.0

    def test_set_quantity(self, model: SQLiteModel):
        """Проверяет, что метод set корректно устанавливает новое количество."""
    
        # 1. Подготовка: Добавляем элемент запаса
        model.stock().add(name='Сахар', category_name='Materials', quantity=100.0, unit_name='kg')
    
        # 2. Действие: Устанавливаем новое количество
        model.stock().set('Сахар', 55.5)

        # 3. Проверка: Получаем элемент и проверяем его количество
        updated_item = model.stock().get('Сахар')
        assert updated_item.quantity == 55.5
    
        # 4. Проверка на ошибку при несуществующем элементе
        with pytest.raises(KeyError):
            model.stock().set('Несуществующий Товар', 10.0)

    def test_update_quantity_positive(self, model: SQLiteModel):
        """Проверяет, что update корректно увеличивает запас."""
        model.stock().add(name='Мука', category_name='Materials', quantity=10.0, unit_name='kg')

        # Увеличение (покупка)
        model.stock().update('Мука', 5.5)
    
        updated_item = model.stock().get('Мука')
        assert updated_item.quantity == 15.5

    def test_update_quantity_negative_success(self, model: SQLiteModel):
        """Проверяет, что update корректно уменьшает запас при достаточном остатке."""
        model.stock().add(name='Мука', category_name='Materials', quantity=10.0, unit_name='kg')

        # Уменьшение (продажа)
        model.stock().update('Мука', -3.0)

        updated_item = model.stock().get('Мука')
        assert updated_item.quantity == 7.0

    def test_update_quantity_negative_failure(self, model: SQLiteModel):
        """Проверяет, что update вызывает ValueError при попытке уйти в минус."""
        model.stock().add(name='Мука', category_name='Materials', quantity=10.0, unit_name='kg')

        # Попытка списания больше, чем есть на складе
        with pytest.raises(ValueError, match="Недостаточно запаса"):
            model.stock().update('Мука', -10.1)
        
        # Проверяем, что количество не изменилось (rollback)
        item_after_fail = model.stock().get('Мука')
        assert item_after_fail.quantity == 10.0
