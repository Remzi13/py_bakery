"""Tests for orders router and repository."""

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def setup_products_for_orders(model):
    """Setup products for order testing."""
    prod_repo = model.products()
    prod_repo.add('Bread', 200, [])
    prod_repo.add('Cake', 300, [])
    prod_repo.add('Donut', 50, [])
    
    bread = prod_repo.by_name('Bread')
    cake = prod_repo.by_name('Cake')
    donut = prod_repo.by_name('Donut')
    
    return {'bread': bread, 'cake': cake, 'donut': donut}


class TestOrdersRepository:
    """Test OrdersRepository methods."""
    
    def test_add_order(self, model, setup_products_for_orders):
        """Test adding a new order."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        
        items = [{'product_id': bread.id, 'quantity': 10.0}]
        repo.add(items)
        
        orders = repo.data()
        assert len(orders) >= 1
        assert any(item['product_id'] == bread.id for o in orders for item in o.items)
    
    def test_add_order_with_multiple_items(self, model, setup_products_for_orders):
        """Test adding orders for multiple products."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        donut = setup_products_for_orders['donut']
        
        repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        repo.add([{'product_id': cake.id, 'quantity': 5.0}])
        repo.add([{'product_id': donut.id, 'quantity': 20.0}])
        
        all_orders = repo.data()
        assert len(all_orders) >= 3
    
    def test_get_order_by_id(self, model, setup_products_for_orders):
        """Test retrieving order by ID."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        
        items = [{'product_id': bread.id, 'quantity': 15.0}]
        order = repo.add(items)
        
        retrieved = repo.by_id(order.id)
        assert retrieved is not None
        assert retrieved.items[0]['product_id'] == bread.id
        assert retrieved.items[0]['quantity'] == 15.0
    
    def test_delete_order(self, model, setup_products_for_orders):
        """Test deleting an order."""
        repo = model.orders()
        donut = setup_products_for_orders['donut']
        
        order = repo.add([{'product_id': donut.id, 'quantity': 50.0}])
        order_id = order.id
        
        repo.delete(order_id)
        
        deleted = repo.by_id(order_id)
        assert deleted is None
    
    def test_get_all_orders(self, model, setup_products_for_orders):
        """Test retrieving all orders."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        donut = setup_products_for_orders['donut']
        
        repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        repo.add([{'product_id': cake.id, 'quantity': 5.0}])
        repo.add([{'product_id': donut.id, 'quantity': 20.0}])
        
        all_orders = repo.data()
        assert len(all_orders) >= 3
    
    def test_get_orders_by_product(self, model, setup_products_for_orders):
        """Test retrieving orders for a specific product."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        
        repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        repo.add([{'product_id': cake.id, 'quantity': 5.0}])
        repo.add([{'product_id': bread.id, 'quantity': 8.0}])
        
        bread_orders = repo.get_by_product(bread.id)
        
        assert len(bread_orders) >= 2
        for o in bread_orders:
            assert any(item['product_id'] == bread.id for item in o.items)
    
    def test_get_pending_orders(self, model, setup_products_for_orders):
        """Test retrieving pending orders."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        
        repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        
        pending = repo.get_pending()
        assert len(pending) >= 1


class TestOrdersRouter:
    """Test orders API router endpoints."""
    
    def test_get_orders_empty(self, client):
        """Test getting orders when none exist."""
        response = client.get("/api/orders/")
        assert response.status_code == 200
    
    def test_get_orders_with_data(self, client, model, setup_products_for_orders):
        """Test getting orders list."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        
        response = client.get("/api/orders/")
        assert response.status_code == 200
    
    def test_get_pending_orders_api(self, client, model, setup_products_for_orders):
        """Test getting pending orders."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        
        response = client.get("/api/orders/pending")
        assert response.status_code == 200
    
    def test_get_order_info(self, client, model, setup_products_for_orders):
        """Test getting order details."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        order = repo.add([{'product_id': bread.id, 'quantity': 10.0}])
        
        response = client.get(f"/api/orders/{order.id}/info")
        assert response.status_code == 200
    
    def test_add_order_with_discount(self, model, setup_products_for_orders):
        """Test adding an order with discount."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        
        items = [{'product_id': bread.id, 'quantity': 10.0}]
        order = repo.add(items, discount=15)
        
        assert order.discount == 15
        retrieved = repo.by_id(order.id)
        assert retrieved.discount == 15
    
    def test_add_order_with_zero_discount(self, model, setup_products_for_orders):
        """Test adding an order with zero discount (default)."""
        repo = model.orders()
        cake = setup_products_for_orders['cake']
        
        items = [{'product_id': cake.id, 'quantity': 5.0}]
        order = repo.add(items)
        
        assert order.discount == 0
        retrieved = repo.by_id(order.id)
        assert retrieved.discount == 0
    
    def test_complete_order_applies_discount(self, model, setup_products_for_orders):
        """Test that completing an order applies the discount to sales."""
        from sql_model.entities import StockCategory, Unit
        
        repo = model.orders()
        sales_repo = model.sales()
        stock_repo = model.stock()
        products_repo = model.products()
        
        # Setup stock category and unit
        category = model.db.query(StockCategory).filter(StockCategory.name == "Materials").first()
        if not category:
            category = StockCategory(name="Materials")
            model.db.add(category)
            model.db.commit()
        
        unit = model.db.query(Unit).filter(Unit.name == "kg").first()
        if not unit:
            unit = Unit(name="kg")
            model.db.add(unit)
            model.db.commit()
        
        # Add stock item (using names, not IDs)
        stock_repo.add("Flour", "Materials", 100.0, "kg")
        flour = stock_repo.get("Flour")
        
        # Create product with recipe
        bread = products_repo.add("TestBread", 200, [
            {"name": "Flour", "quantity": 0.5, "conversion_factor": 1.0}
        ])
        
        # Create order with 20% discount
        items = [{'product_id': bread.id, 'quantity': 5.0}]
        order = repo.add(items, discount=20)
        
        # Complete the order
        repo.complete(order.id)
        
        # Check that sale was created with correct discount
        sales = sales_repo.data()
        latest_sale = sales[-1]
        assert latest_sale.discount == 20
        assert latest_sale.product_id == bread.id
        assert latest_sale.quantity == 5.0
    
    def test_get_all_orders_includes_discount(self, model, setup_products_for_orders):
        """Test that retrieving all orders includes discount field."""
        repo = model.orders()
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        
        repo.add([{'product_id': bread.id, 'quantity': 10.0}], discount=10)
        repo.add([{'product_id': cake.id, 'quantity': 5.0}], discount=25)
        
        all_orders = repo.data()
        assert all(hasattr(order, 'discount') for order in all_orders)
    
    def test_pending_orders_includes_discount(self, model, setup_products_for_orders):
        """Test that pending orders include discount field."""
        repo = model.orders()
        donut = setup_products_for_orders['donut']
        
        repo.add([{'product_id': donut.id, 'quantity': 20.0}], discount=15)
        
        pending = repo.get_pending()
        assert len(pending) >= 1
        assert all(hasattr(order, 'discount') for order in pending)
