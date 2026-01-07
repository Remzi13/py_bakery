import pytest
import sqlite3

from tests.core import conn, get_unit_by_name, sqlite3, SQLiteModel, TEST_DB

from repositories.stock import StockRepository
class TestStockRepository:
    
    @pytest.fixture
    def repo(self, conn: sqlite3.Connection) -> StockRepository:
        return StockRepository(conn)

    def test_add_and_get(self, repo: StockRepository):
        repo.add(name='Мешок', category_name='Packaging', quantity=100.0, unit_name='pc')
        item = repo.get('Мешок')
        
        assert repo.by_id(item.id).name == item.name
        assert item is not None
        assert item.name == 'Мешок'
        assert item.quantity == 100.0
        assert repo.len() == 1
        
    def test_update_quantity(self, repo: StockRepository):
        repo.add(name='Вода', category_name='Materials', quantity=50.0, unit_name='l')
        
        # Оприходование
        repo.update('Вода', 10.0)
        assert repo.get('Вода').quantity == 60.0
        
        # Списание
        repo.update('Вода', -20.0)
        assert repo.get('Вода').quantity == 40.0
        
    def test_update_negative_balance(self, repo: StockRepository):
        repo.add(name='Масло', category_name='Materials', quantity=10.0, unit_name='kg')
        
        # Попытка списать больше, чем есть
        with pytest.raises(ValueError, match="Недостаточно запаса для 'Масло'. Требуется списание 100.00, текущий остаток 10.00."):
            repo.update('Масло', -100.0)

    def test_data(self, repo: StockRepository):
        repo.add(name='Мука', category_name='Materials', quantity=100.0, unit_name='kg')
        repo.add(name='Яйцо', category_name='Materials', quantity=50.0, unit_name='pc')
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Мука'
        assert data[1].quantity == 50.0

    def test_set_quantity(self, repo: StockRepository):
        """Проверяет, что метод set корректно устанавливает новое количество."""
    
        # 1. Подготовка: Добавляем элемент запаса
        repo.add(name='Сахар', category_name='Materials', quantity=100.0, unit_name='kg')
    
        # 2. Действие: Устанавливаем новое количество
        repo.set('Сахар', 55.5)
    
        # 3. Проверка: Получаем элемент и проверяем его количество
        updated_item = repo.get('Сахар')
        assert updated_item.quantity == 55.5
    
        # 4. Проверка на ошибку при несуществующем элементе
        with pytest.raises(KeyError):
            repo.set('Несуществующий Товар', 10.0)

    def test_update_quantity_positive(self, repo: StockRepository):
        """Проверяет, что update корректно увеличивает запас."""
        repo.add(name='Мука', category_name='Materials', quantity=10.0, unit_name='kg')
    
        # Увеличение (покупка)
        repo.update('Мука', 5.5)
    
        updated_item = repo.get('Мука')
        assert updated_item.quantity == 15.5

    def test_update_quantity_negative_success(self, repo: StockRepository):
        """Проверяет, что update корректно уменьшает запас при достаточном остатке."""
        repo.add(name='Мука', category_name='Materials', quantity=10.0, unit_name='kg')

        # Уменьшение (продажа)
        repo.update('Мука', -3.0)

        updated_item = repo.get('Мука')
        assert updated_item.quantity == 7.0

    def test_update_quantity_negative_failure(self, repo: StockRepository):
        """Проверяет, что update вызывает ValueError при попытке уйти в минус."""
        repo.add(name='Мука', category_name='Materials', quantity=10.0, unit_name='kg')

        # Попытка списания больше, чем есть на складе
        with pytest.raises(ValueError, match="Недостаточно запаса"):
            repo.update('Мука', -10.1)
        
        # Проверяем, что количество не изменилось (rollback)
        item_after_fail = repo.get('Мука')
        assert item_after_fail.quantity == 10.0
