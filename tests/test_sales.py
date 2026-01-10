import pytest

from tests.core import SQLiteModel, conn, model

class TestSalesRepository:

    @pytest.fixture(autouse=True)
    def setup_stock_and_products(self, model: SQLiteModel):
        # 1. Зависимости
        model.stock().add('Мука', "Materials", 10, 'kg')        
        
        # 2. Продукт: 1 Булочка = 0.5 kg Муки
        recipe = [{'name': 'Мука', 'quantity': 0.5}]
        model.products().add(name='Булочка', price=80, materials=recipe)
        
    def test_add_sale_and_stock_deduction(self, model: SQLiteModel):
        repo = model.sales()
        initial_stock = model.stock().get('Мука').quantity # 10.0
        
        # Продажа 4-х Булочек. Списание: 4 * 0.5 kg = 2.0 kg
        repo.add(name='Булочка', price=80, quantity=4.0, discount=10) 
        
        final_stock = model.stock().get('Мука').quantity # 10.0 - 2.0 = 8.0
        
        assert repo.len() == 1
        sale = repo.data()[0]
        assert sale.product_name == 'Булочка'
        assert sale.quantity == 4.0
        assert final_stock == 8.0
        
    def test_sale_denied_insufficient_stock(self, model: SQLiteModel):
        repo = model.sales()
        # Попытка продать 30 Булочек. Списание: 30 * 0.5 kg = 15.0 kg (есть 10.0 kg)
        
        with pytest.raises(ValueError, match=r"Недостаточно запаса для 'Мука'. Требуется списание 15.00, текущий остаток 10.00."):
            repo.add(name='Булочка', price=80, quantity=30.0, discount=0)
            
        # Проверка, что транзакция была откатана
        assert model.sales().empty() is True
        assert model.stock().get('Мука').quantity == 10.0 # Запасы не должны измениться
    
    def test_data(self, model: SQLiteModel):
        repo = model.sales()
        # Используем продукт, созданный в setup_stock_and_products
        
        repo.add(name='Булочка', price=80, quantity=1.0, discount=0) 
        repo.add(name='Булочка', price=80, quantity=2.0, discount=10) 
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].quantity == 1.0
        assert data[1].discount == 10
        assert data[1].product_name == 'Булочка'
