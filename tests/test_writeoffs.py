"""Tests for write-offs router and repository."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sql_model.entities import StockItem, StockCategory, Unit


@pytest.fixture
def setup_stock_data(model):
    """Setup stock items for write-off testing."""
    model.stock().add('Flour', 'Materials', 100.0, 'kg')
    item = model.stock().get('Flour')
    return {'flour': item}


class TestWriteOffsRepository:
    """Test WriteOffsRepository methods."""
    
    def test_add_writeoff(self, model, setup_stock_data):
        """Test adding a new write-off."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        
        repo.add(item.id, 'stock', 5.0, 'Expired')
        
        writeoffs = repo.data()
        assert len(writeoffs) >= 1
        assert any(w.stock_item_id == item.id for w in writeoffs)
        
        # Check stock deduction
        updated_item = model.stock().get('Flour')
        assert updated_item.quantity == 95.0
    
    def test_add_writeoff_with_reason(self, model, setup_stock_data):
        """Test adding a write-off with a specific reason."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        repo.add(item.id, 'stock', 2.0, 'Damaged Packaging')
        
        writeoff = repo.data()[0]
        assert writeoff.quantity == 2.0
        assert writeoff.reason == 'Damaged Packaging'
    
    def test_get_writeoff_by_id(self, model, setup_stock_data):
        """Test retrieving write-off by ID."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        
        repo.add(item.id, 'stock', 1.0, 'Test')
        wo = repo.data()[0]
        
        retrieved = repo.by_id(wo.id)
        assert retrieved is not None
        assert retrieved.quantity == 1.0
    
    def test_delete_writeoff(self, model, setup_stock_data):
        """Test deleting a write-off record."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        
        repo.add(item.id, 'stock', 3.0, 'To Delete')
        wo = repo.data()[0]
        wo_id = wo.id
        
        repo.delete(wo_id)
        
        deleted = repo.by_id(wo_id)
        assert deleted is None
    
    def test_get_all_writeoffs(self, model, setup_stock_data):
        """Test retrieving all write-offs."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        
        repo.add(item.id, 'stock', 1.0, 'R1')
        repo.add(item.id, 'stock', 2.0, 'R2')
        
        all_writeoffs = repo.data()
        assert len(all_writeoffs) >= 2
    
    def test_get_writeoffs_by_stock(self, model, setup_stock_data):
        """Test retrieving write-offs for a specific stock item."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        
        repo.add(item.id, 'stock', 1.0, 'R1')
        
        item_writeoffs = repo.get_by_stock_item(item.id)
        assert len(item_writeoffs) >= 1


class TestWriteOffsRouter:
    """Test write-offs API router endpoints."""
    
    def test_get_writeoffs_empty(self, client):
        """Test getting write-offs when none exist."""
        response = client.get("/api/writeoffs/")
        assert response.status_code == 200
    
    def test_get_writeoffs_with_data(self, client, model, setup_stock_data):
        """Test getting write-offs list."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        repo.add(item.id, 'stock', 5.0, 'Test')
        
        response = client.get("/api/writeoffs/")
        assert response.status_code == 200
    
    def test_get_writeoffs_by_date(self, client, model, setup_stock_data):
        """Test getting write-offs for a specific date."""
        repo = model.writeoffs()
        item = setup_stock_data['flour']
        repo.add(item.id, 'stock', 5.0, 'Test')
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/writeoffs/?search={today}")
        assert response.status_code == 200
    
    def test_get_writeoff_by_stock(self, client, model, setup_stock_data):
        """Test getting write-offs filtered by stock item."""
        item = setup_stock_data['flour']
        response = client.get(f"/api/writeoffs/?stock_item_id={item.id}")
        assert response.status_code == 200
