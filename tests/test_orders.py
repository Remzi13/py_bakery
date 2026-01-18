"""Tests for orders router and repository."""

import pytest
from sqlalchemy.orm import Session
from repositories.orders import OrdersRepository
from repositories.products import ProductsRepository


@pytest.fixture
def setup_products_for_orders(test_db: Session):
    """Setup products for order testing."""
    prod_repo = ProductsRepository(test_db)
    prod_repo.add('Bread', 200, [])
    prod_repo.add('Cake', 300, [])
    prod_repo.add('Donut', 50, [])
    
    bread = prod_repo.by_name('Bread')
    cake = prod_repo.by_name('Cake')
    donut = prod_repo.by_name('Donut')
    
    return {'bread': bread, 'cake': cake, 'donut': donut}


class TestOrdersRepository:
    """Test OrdersRepository methods."""
    
    def test_add_order(self, test_db: Session, setup_products_for_orders):
        """Test adding a new order."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        
        repo.add(bread.id, 10.0)
        
        orders = repo.data()
        assert len(orders) >= 1
        assert any(o.product_id == bread.id for o in orders)
    
    def test_add_order_with_multiple_items(self, test_db: Session, setup_products_for_orders):
        """Test adding orders for multiple products."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        donut = setup_products_for_orders['donut']
        
        repo.add(bread.id, 10.0)
        repo.add(cake.id, 5.0)
        repo.add(donut.id, 20.0)
        
        all_orders = repo.data()
        assert len(all_orders) >= 3
    
    def test_get_order_by_id(self, test_db: Session, setup_products_for_orders):
        """Test retrieving order by ID."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        
        repo.add(bread.id, 15.0)
        order = repo.data()[0]
        
        retrieved = repo.by_id(order.id)
        assert retrieved is not None
        assert retrieved.product_id == bread.id
        assert retrieved.quantity == 15.0
    
    def test_update_order_quantity(self, test_db: Session, setup_products_for_orders):
        """Test updating order quantity."""
        repo = OrdersRepository(test_db)
        cake = setup_products_for_orders['cake']
        
        repo.add(cake.id, 8.0)
        order = repo.data()[0]
        
        repo.update(order.id, quantity=12.0)
        
        updated = repo.by_id(order.id)
        assert updated.quantity == 12.0
    
    def test_delete_order(self, test_db: Session, setup_products_for_orders):
        """Test deleting an order."""
        repo = OrdersRepository(test_db)
        donut = setup_products_for_orders['donut']
        
        repo.add(donut.id, 50.0)
        order = repo.data()[0]
        order_id = order.id
        
        repo.delete(order_id)
        
        deleted = repo.by_id(order_id)
        assert deleted is None
    
    def test_get_all_orders(self, test_db: Session, setup_products_for_orders):
        """Test retrieving all orders."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        donut = setup_products_for_orders['donut']
        
        repo.add(bread.id, 10.0)
        repo.add(cake.id, 5.0)
        repo.add(donut.id, 20.0)
        
        all_orders = repo.data()
        assert len(all_orders) >= 3
    
    def test_get_orders_by_product(self, test_db: Session, setup_products_for_orders):
        """Test retrieving orders for a specific product."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        cake = setup_products_for_orders['cake']
        
        repo.add(bread.id, 10.0)
        repo.add(cake.id, 5.0)
        repo.add(bread.id, 8.0)
        
        bread_orders = repo.get_by_product(bread.id)
        
        assert len(bread_orders) >= 2
        assert all(o.product_id == bread.id for o in bread_orders)
    
    def test_get_pending_orders(self, test_db: Session, setup_products_for_orders):
        """Test retrieving pending orders."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        
        repo.add(bread.id, 10.0)
        order = repo.data()[0]
        
        # Check if order is marked as pending (status = 'pending')
        pending = repo.get_pending()
        assert len(pending) >= 1


class TestOrdersRouter:
    """Test orders API router endpoints."""
    
    def test_get_orders_empty(self, client):
        """Test getting orders when none exist."""
        response = client.get("/api/orders/")
        assert response.status_code == 200
    
    def test_get_orders_with_data(self, client, test_db: Session, setup_products_for_orders):
        """Test getting orders list."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        repo.add(bread.id, 10.0)
        
        response = client.get("/api/orders/")
        assert response.status_code == 200
    
    def test_get_pending_orders(self, client, test_db: Session, setup_products_for_orders):
        """Test getting pending orders."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        repo.add(bread.id, 10.0)
        
        response = client.get("/api/orders/?status=pending")
        assert response.status_code == 200
    
    def test_get_new_order_form(self, client):
        """Test getting new order form."""
        response = client.get("/api/orders/new")
        assert response.status_code == 200
    
    def test_get_order_info(self, client, test_db: Session, setup_products_for_orders):
        """Test getting order details."""
        repo = OrdersRepository(test_db)
        bread = setup_products_for_orders['bread']
        repo.add(bread.id, 10.0)
        
        order = repo.data()[0]
        response = client.get(f"/api/orders/{order.id}/info")
        assert response.status_code == 200
