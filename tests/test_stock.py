"""Tests for stock router and repository."""

import pytest
from sqlalchemy.orm import Session
from repositories.stock import StockRepository
from sql_model.entities import StockItem, StockCategory, Unit


@pytest.fixture
def setup_categories_and_units(test_db: Session):
    """Setup categories and units for testing."""
    materials_cat = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
    kg_unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
    
    return {'category': materials_cat, 'unit': kg_unit}


class TestStockRepository:
    """Test StockRepository methods."""
    
    def test_add_stock_item(self, test_db: Session, setup_categories_and_units):
        """Test adding a new stock item."""
        repo = StockRepository(test_db)
        
        repo.add('Flour', 'Materials', 100.0, 'kg')
        
        item = repo.by_name('Flour')
        assert item is not None
        assert item.name == 'Flour'
        assert item.quantity == 100.0
    
    def test_add_stock_with_invalid_category(self, test_db: Session):
        """Test adding stock with invalid category."""
        repo = StockRepository(test_db)
        
        with pytest.raises(ValueError, match="Category 'InvalidCategory' not found"):
            repo.add('Item', 'InvalidCategory', 100.0, 'kg')
    
    def test_add_stock_with_invalid_unit(self, test_db: Session, setup_categories_and_units):
        """Test adding stock with invalid unit."""
        repo = StockRepository(test_db)
        
        with pytest.raises(ValueError, match="Unit 'invalid_unit' not found"):
            repo.add('Item', 'Materials', 100.0, 'invalid_unit')
    
    def test_get_stock_by_id(self, test_db: Session, setup_categories_and_units):
        """Test retrieving stock item by ID."""
        repo = StockRepository(test_db)
        
        repo.add('Sugar', 'Materials', 50.0, 'kg')
        item = repo.by_name('Sugar')
        
        retrieved = repo.by_id(item.id)
        assert retrieved is not None
        assert retrieved.name == 'Sugar'
        assert retrieved.quantity == 50.0
    
    def test_update_stock_quantity(self, test_db: Session, setup_categories_and_units):
        """Test updating stock quantity."""
        repo = StockRepository(test_db)
        
        repo.add('Butter', 'Materials', 30.0, 'kg')
        item = repo.by_name('Butter')
        
        repo.set_quantity(item.id, 45.0)
        
        updated = repo.by_id(item.id)
        assert updated.quantity == 45.0
    
    def test_increase_stock_quantity(self, test_db: Session, setup_categories_and_units):
        """Test increasing stock quantity."""
        repo = StockRepository(test_db)
        
        repo.add('Eggs', 'Materials', 100.0, 'pc')
        item = repo.by_name('Eggs')
        
        repo.add_quantity(item.id, 50.0)
        
        updated = repo.by_id(item.id)
        assert updated.quantity == 150.0
    
    def test_decrease_stock_quantity(self, test_db: Session, setup_categories_and_units):
        """Test decreasing stock quantity."""
        repo = StockRepository(test_db)
        
        repo.add('Salt', 'Materials', 100.0, 'kg')
        item = repo.by_name('Salt')
        
        repo.add_quantity(item.id, -25.0)
        
        updated = repo.by_id(item.id)
        assert updated.quantity == 75.0
    
    def test_delete_stock_item(self, test_db: Session, setup_categories_and_units):
        """Test deleting a stock item."""
        repo = StockRepository(test_db)
        
        repo.add('Temporary', 'Materials', 10.0, 'kg')
        item = repo.by_name('Temporary')
        item_id = item.id
        
        repo.delete(item_id)
        
        deleted = repo.by_id(item_id)
        assert deleted is None
    
    def test_get_all_stock_items(self, test_db: Session, setup_categories_and_units):
        """Test retrieving all stock items."""
        repo = StockRepository(test_db)
        
        repo.add('Flour', 'Materials', 100.0, 'kg')
        repo.add('Sugar', 'Materials', 50.0, 'kg')
        repo.add('Eggs', 'Materials', 200.0, 'pc')
        
        all_items = repo.data()
        assert len(all_items) >= 3
        
        names = [item.name for item in all_items]
        assert 'Flour' in names
        assert 'Sugar' in names
        assert 'Eggs' in names
    
    def test_get_stock_by_category(self, test_db: Session, setup_categories_and_units):
        """Test retrieving stock items by category."""
        repo = StockRepository(test_db)
        
        repo.add('Flour', 'Materials', 100.0, 'kg')
        repo.add('Sugar', 'Materials', 50.0, 'kg')
        
        materials_items = repo.get_by_category('Materials')
        
        assert len(materials_items) >= 2
        assert all(item.category_id == materials_items[0].category_id for item in materials_items)
    
    def test_update_stock_item_details(self, test_db: Session, setup_categories_and_units):
        """Test updating stock item details."""
        repo = StockRepository(test_db)
        
        repo.add('Chocolate', 'Materials', 25.0, 'kg')
        item = repo.by_name('Chocolate')
        
        repo.update(item.id, name='Dark Chocolate', quantity=30.0)
        
        updated = repo.by_id(item.id)
        assert updated.name == 'Dark Chocolate'
        assert updated.quantity == 30.0


class TestStockRouter:
    """Test stock API router endpoints."""
    
    def test_get_stock_empty(self, client):
        """Test getting stock when no items exist."""
        response = client.get("/api/stock/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_stock_with_data(self, client, test_db: Session, setup_categories_and_units):
        """Test getting stock list."""
        repo = StockRepository(test_db)
        repo.add('Flour', 'Materials', 100.0, 'kg')
        
        response = client.get("/api/stock/")
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= 1
        assert any(item['name'] == 'Flour' for item in items)
    
    def test_get_stock_with_search(self, client, test_db: Session, setup_categories_and_units):
        """Test searching stock items."""
        repo = StockRepository(test_db)
        repo.add('Flour', 'Materials', 100.0, 'kg')
        repo.add('Sugar', 'Materials', 50.0, 'kg')
        repo.add('Eggs', 'Materials', 200.0, 'pc')
        
        response = client.get("/api/stock/?search=flour")
        assert response.status_code == 200
        
        items = response.json()
        for item in items:
            assert 'flour' in item['name'].lower()
    
    def test_get_stock_new_form(self, client):
        """Test getting new stock item form."""
        response = client.get("/api/stock/new")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
    
    def test_get_stock_edit_form_existing(self, client, test_db: Session, setup_categories_and_units):
        """Test getting edit form for existing stock item."""
        repo = StockRepository(test_db)
        repo.add('Flour', 'Materials', 100.0, 'kg')
        
        item = repo.by_name('Flour')
        response = client.get(f"/api/stock/{item.id}/edit")
        assert response.status_code == 200
    
    def test_get_stock_edit_form_non_existing(self, client):
        """Test getting edit form for non-existent stock item."""
        response = client.get("/api/stock/99999/edit")
        assert response.status_code == 404
    
    def test_get_stock_by_category(self, client, test_db: Session, setup_categories_and_units):
        """Test getting stock filtered by category."""
        repo = StockRepository(test_db)
        repo.add('Flour', 'Materials', 100.0, 'kg')
        repo.add('Sugar', 'Materials', 50.0, 'kg')
        
        response = client.get("/api/stock/?category=Materials")
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= 2
