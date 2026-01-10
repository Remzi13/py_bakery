import pytest
from tests.core import SQLiteModel, conn, model

class TestOrdersRepository:

    @pytest.fixture(autouse=True)
    def setup_data(self, model: SQLiteModel):
        # 1. Materials
        model.stock().add('Flour',"Materials", 10, 'kg')        
        
        # 2. Products
        recipe = [{'name': 'Flour', 'quantity': 0.5}]
        model.products().add(name='Bread', price=100, materials=recipe)
        self.bread_id = model.products().by_name('Bread').id

    def test_create_order(self, model: SQLiteModel):
        repo = model.orders()
        items = [{'product_id': self.bread_id, 'quantity': 2.0}]
        order = repo.add(items=items, completion_date='2026-01-10 12:00', additional_info='Test order')
        
        assert order.status == 'pending'
        # re-fetch to get items (add returns Order dataclass which might not have items yet)
        full_order = repo.by_id(order.id)
        assert len(full_order.items) == 1
        assert full_order.items[0]['product_name'] == 'Bread'
        assert full_order.items[0]['quantity'] == 2.0
        assert full_order.completion_date == '2026-01-10 12:00'

    def test_complete_order_success(self, model: SQLiteModel):
        repo = model.orders()
        items = [{'product_id': self.bread_id, 'quantity': 2.0}]
        order = repo.add(items=items, completion_date='2026-01-10 12:00')
        
        initial_stock = model.stock().get('Flour').quantity # 10.0
        
        success = repo.complete(order.id)
        assert success is True
        
        # Check order status
        completed_order = repo.by_id(order.id)
        assert completed_order.status == 'completed'
        
        # Check stock deduction: 2.0 * 0.5 = 1.0 kg
        final_stock = model.stock().get('Flour').quantity
        assert final_stock == 9.0
        
        # Check sale record
        sales = model.sales().data()
        assert len(sales) == 1
        assert sales[0].product_name == 'Bread'
        assert sales[0].quantity == 2.0

    def test_complete_order_atomicity_failure(self, model: SQLiteModel):
        repo = model.orders()
        # Create an order that requires more stock than available
        items = [{'product_id': self.bread_id, 'quantity': 30.0}] # Needs 15 kg, have 10 kg
        order = repo.add(items=items, completion_date='2026-01-10 12:00')
        
        initial_stock = model.stock().get('Flour').quantity # 10.0
        
        with pytest.raises(ValueError):
            repo.complete(order.id)
            
        # Check that order status is still pending (transaction rolled back)
        pending_order = repo.by_id(order.id)
        assert pending_order.status == 'pending'
        
        # Check stock not changed
        assert model.stock().get('Flour').quantity == 10.0
        
        # Check no sales recorded
        assert model.sales().empty() is True
