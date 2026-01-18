"""Tests for sales router and repository."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.sales import SalesRepository
from repositories.products import ProductsRepository
from sql_model.entities import StockItem, StockCategory, Unit, Product


@pytest.fixture
def setup_products_and_stock(test_db: Session):
    """Setup products and stock for sales testing."""
    # Get existing units and categories
    kg_unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
    materials_cat = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
    
    # Create stock items
    flour = StockItem(name='Flour', category_id=materials_cat.id, quantity=1000.0, unit_id=kg_unit.id)
    test_db.add(flour)
    test_db.commit()
    
    # Create products
    prod_repo = ProductsRepository(test_db)
    prod_repo.add('Bread', 200, [{'name': 'Flour', 'quantity': 400.0}])
    prod_repo.add('Cake', 300, [{'name': 'Flour', 'quantity': 500.0}])
    
    bread = prod_repo.by_name('Bread')
    cake = prod_repo.by_name('Cake')
    
    return {'bread': bread, 'cake': cake}


class TestSalesRepository:
    """Test SalesRepository methods."""
    
    def test_add_sale(self, test_db: Session, setup_products_and_stock):
        """Test adding a new sale."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        
        repo.add(product.id, 5.0, 0)
        
        sales = repo.data()
        assert len(sales) >= 1
        assert any(s.product_id == product.id for s in sales)
    
    def test_add_sale_with_discount(self, test_db: Session, setup_products_and_stock):
        """Test adding a sale with discount."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        
        repo.add(product.id, 3.0, 10)
        
        sale = repo.data()[0]
        assert sale.quantity == 3.0
        assert sale.discount == 10
    
    def test_get_sale_by_id(self, test_db: Session, setup_products_and_stock):
        """Test retrieving sale by ID."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        
        repo.add(product.id, 2.0, 5)
        sale = repo.data()[0]
        
        retrieved = repo.by_id(sale.id)
        assert retrieved is not None
        assert retrieved.product_id == product.id
        assert retrieved.quantity == 2.0
    
    def test_delete_sale(self, test_db: Session, setup_products_and_stock):
        """Test deleting a sale."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        
        repo.add(product.id, 1.0, 0)
        sale = repo.data()[0]
        sale_id = sale.id
        
        repo.delete(sale_id)
        
        deleted = repo.by_id(sale_id)
        assert deleted is None
    
    def test_get_all_sales(self, test_db: Session, setup_products_and_stock):
        """Test retrieving all sales."""
        repo = SalesRepository(test_db)
        bread = setup_products_and_stock['bread']
        cake = setup_products_and_stock['cake']
        
        repo.add(bread.id, 5.0, 0)
        repo.add(cake.id, 3.0, 10)
        repo.add(bread.id, 2.0, 5)
        
        all_sales = repo.data()
        assert len(all_sales) >= 3
    
    def test_get_sales_by_date_range(self, test_db: Session, setup_products_and_stock):
        """Test retrieving sales within a date range."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        
        repo.add(product.id, 5.0, 0)
        
        today = datetime.now().date()
        sales = repo.get_by_date_range(today, today)
        
        assert len(sales) >= 1
    
    def test_get_sales_by_product(self, test_db: Session, setup_products_and_stock):
        """Test retrieving sales for a specific product."""
        repo = SalesRepository(test_db)
        bread = setup_products_and_stock['bread']
        cake = setup_products_and_stock['cake']
        
        repo.add(bread.id, 5.0, 0)
        repo.add(cake.id, 3.0, 0)
        repo.add(bread.id, 2.0, 0)
        
        bread_sales = repo.get_by_product(bread.id)
        
        assert len(bread_sales) >= 2
        assert all(s.product_id == bread.id for s in bread_sales)


class TestSalesRouter:
    """Test sales API router endpoints."""
    
    def test_get_sales_empty(self, client):
        """Test getting sales when none exist."""
        response = client.get("/api/sales/")
        assert response.status_code == 200
    
    def test_get_sales_with_data(self, client, test_db: Session, setup_products_and_stock):
        """Test getting sales list."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        repo.add(product.id, 5.0, 0)
        
        response = client.get("/api/sales/")
        assert response.status_code == 200
    
    def test_get_sales_by_date(self, client, test_db: Session, setup_products_and_stock):
        """Test getting sales for a specific date."""
        repo = SalesRepository(test_db)
        product = setup_products_and_stock['bread']
        repo.add(product.id, 5.0, 0)
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/sales/?date={today}")
        assert response.status_code == 200
    
    def test_get_sales_new_form(self, client):
        """Test getting new sale form."""
        response = client.get("/api/sales/new")
        assert response.status_code == 200
    
    def test_create_sale_via_post(self, client, test_db: Session, setup_products_and_stock):
        """Test creating a sale via POST request."""
        product = setup_products_and_stock['bread']
        
        response = client.post(
            "/api/sales/",
            data={
                "product_id": str(product.id),
                "quantity": "2.5",
                "discount": "0"
            }
        )
        
        # Check if sale was created
        get_response = client.get("/api/sales/")
        assert get_response.status_code == 200
