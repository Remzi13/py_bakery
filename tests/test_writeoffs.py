"""Tests for write-offs router and repository."""

import pytest
from sqlalchemy.orm import Session
from repositories.write_offs import WriteOffsRepository
from repositories.stock import StockRepository
from sql_model.entities import Unit, StockCategory


@pytest.fixture
def setup_writeoff_data(test_db: Session):
    """Setup stock items for write-off testing."""
    kg_unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
    materials_cat = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
    
    stock_repo = StockRepository(test_db)
    stock_repo.add('Flour', 'Materials', 100.0, 'kg')
    stock_repo.add('Sugar', 'Materials', 50.0, 'kg')
    
    flour = stock_repo.by_name('Flour')
    sugar = stock_repo.by_name('Sugar')
    
    return {'flour': flour, 'sugar': sugar, 'unit': kg_unit, 'category': materials_cat}


class TestWriteOffsRepository:
    """Test WriteOffsRepository methods."""
    
    def test_add_writeoff(self, test_db: Session, setup_writeoff_data):
        """Test adding a new write-off."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        
        repo.add(flour.id, 5.0, 'Damaged product')
        
        writeoffs = repo.data()
        assert len(writeoffs) >= 1
        assert any(w.stock_id == flour.id for w in writeoffs)
    
    def test_add_writeoff_with_reason(self, test_db: Session, setup_writeoff_data):
        """Test adding write-off with reason."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        
        repo.add(flour.id, 2.5, 'Expired batch')
        
        writeoff = repo.data()[0]
        assert writeoff.quantity == 2.5
        assert writeoff.reason == 'Expired batch'
    
    def test_get_writeoff_by_id(self, test_db: Session, setup_writeoff_data):
        """Test retrieving write-off by ID."""
        repo = WriteOffsRepository(test_db)
        sugar = setup_writeoff_data['sugar']
        
        repo.add(sugar.id, 3.0, 'Test reason')
        writeoff = repo.data()[0]
        
        retrieved = repo.by_id(writeoff.id)
        assert retrieved is not None
        assert retrieved.stock_id == sugar.id
        assert retrieved.quantity == 3.0
    
    def test_delete_writeoff(self, test_db: Session, setup_writeoff_data):
        """Test deleting a write-off."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        
        repo.add(flour.id, 1.0, 'Cleanup')
        writeoff = repo.data()[0]
        writeoff_id = writeoff.id
        
        repo.delete(writeoff_id)
        
        deleted = repo.by_id(writeoff_id)
        assert deleted is None
    
    def test_get_all_writeoffs(self, test_db: Session, setup_writeoff_data):
        """Test retrieving all write-offs."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        sugar = setup_writeoff_data['sugar']
        
        repo.add(flour.id, 5.0, 'Reason 1')
        repo.add(sugar.id, 2.0, 'Reason 2')
        repo.add(flour.id, 3.0, 'Reason 3')
        
        all_writeoffs = repo.data()
        assert len(all_writeoffs) >= 3
    
    def test_get_writeoffs_by_stock(self, test_db: Session, setup_writeoff_data):
        """Test retrieving write-offs for a specific stock item."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        sugar = setup_writeoff_data['sugar']
        
        repo.add(flour.id, 5.0, 'Reason 1')
        repo.add(sugar.id, 2.0, 'Reason 2')
        repo.add(flour.id, 3.0, 'Reason 3')
        
        flour_writeoffs = repo.get_by_stock(flour.id)
        
        assert len(flour_writeoffs) >= 2
        assert all(w.stock_id == flour.id for w in flour_writeoffs)


class TestWriteOffsRouter:
    """Test write-offs API router endpoints."""
    
    def test_get_writeoffs_empty(self, client):
        """Test getting write-offs when none exist."""
        response = client.get("/api/writeoffs/")
        assert response.status_code == 200
    
    def test_get_writeoffs_with_data(self, client, test_db: Session, setup_writeoff_data):
        """Test getting write-offs list."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        repo.add(flour.id, 5.0, 'Damaged')
        
        response = client.get("/api/writeoffs/")
        assert response.status_code == 200
    
    def test_get_writeoffs_by_date(self, client, test_db: Session, setup_writeoff_data):
        """Test getting write-offs filtered by date."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        repo.add(flour.id, 5.0, 'Damaged')
        
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/writeoffs/?date={today}")
        assert response.status_code == 200
    
    def test_get_new_writeoff_form(self, client):
        """Test getting new write-off form."""
        response = client.get("/api/writeoffs/new")
        assert response.status_code == 200
    
    def test_get_writeoff_by_stock(self, client, test_db: Session, setup_writeoff_data):
        """Test getting write-offs for a stock item."""
        repo = WriteOffsRepository(test_db)
        flour = setup_writeoff_data['flour']
        repo.add(flour.id, 5.0, 'Damaged')
        
        response = client.get(f"/api/writeoffs/?stock_id={flour.id}")
        assert response.status_code == 200
