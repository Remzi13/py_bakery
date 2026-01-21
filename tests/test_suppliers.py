"""Tests for suppliers router and repository."""

import pytest
from sqlalchemy.orm import Session
from repositories.suppliers import SuppliersRepository


class TestSuppliersRepository:
    """Test SuppliersRepository methods."""
    
    def test_add_supplier(self, test_db: Session):
        """Test adding a new supplier."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Local Bakery Supply', email='contact@bakery.com', phone='555-1234')
        
        supplier = repo.by_name('Local Bakery Supply')
        assert supplier is not None
        assert supplier.name == 'Local Bakery Supply'
        assert supplier.email == 'contact@bakery.com'
    
    def test_add_supplier_minimal(self, test_db: Session):
        """Test adding supplier with minimal information."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Simple Supplier')
        
        supplier = repo.by_name('Simple Supplier')
        assert supplier is not None
        assert supplier.name == 'Simple Supplier'
    
    def test_get_supplier_by_id(self, test_db: Session):
        """Test retrieving supplier by ID."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Supplier A', email='a@supplier.com', phone='555-0001')
        supplier = repo.by_name('Supplier A')
        
        retrieved = repo.by_id(supplier.id)
        assert retrieved is not None
        assert retrieved.name == 'Supplier A'
        assert retrieved.email == 'a@supplier.com'
    
    def test_update_supplier(self, test_db: Session):
        """Test updating a supplier."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Old Name', email='old@email.com', phone='555-0001')
        supplier = repo.by_name('Old Name')
        
        repo.update(supplier.id, name='New Name', email='new@email.com', phone='555-9999')
        
        updated = repo.by_id(supplier.id)
        assert updated.name == 'New Name'
        assert updated.email == 'new@email.com'
    
    def test_delete_supplier(self, test_db: Session):
        """Test deleting a supplier."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Temporary Supplier', email='temp@supplier.com', phone='555-9999')
        supplier = repo.by_name('Temporary Supplier')
        supplier_id = supplier.id
        
        repo.delete_by_id(supplier_id)
        
        deleted = repo.by_id(supplier_id)
        assert deleted is None
    
    def test_get_all_suppliers(self, test_db: Session):
        """Test retrieving all suppliers."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Supplier 1', email='sup1@email.com', phone='555-0001')
        repo.add(name='Supplier 2', email='sup2@email.com', phone='555-0002')
        repo.add(name='Supplier 3', email='sup3@email.com', phone='555-0003')
        
        all_suppliers = repo.data()
        assert len(all_suppliers) >= 3
        
        names = [s.name for s in all_suppliers]
        assert 'Supplier 1' in names
        assert 'Supplier 2' in names
        assert 'Supplier 3' in names
    
    def test_get_supplier_by_name(self, test_db: Session):
        """Test retrieving supplier by name."""
        repo = SuppliersRepository(test_db)
        
        repo.add(name='Unique Supplier', email='unique@email.com', phone='555-1111')
        
        supplier = repo.by_name('Unique Supplier')
        assert supplier is not None
        assert supplier.name == 'Unique Supplier'
    
    def test_get_nonexistent_supplier(self, test_db: Session):
        """Test retrieving non-existent supplier."""
        repo = SuppliersRepository(test_db)
        
        supplier = repo.by_id(99999)
        assert supplier is None


class TestSuppliersRouter:
    """Test suppliers API router endpoints."""
    
    def test_get_suppliers_empty(self, client):
        """Test getting suppliers when none exist."""
        # Ensure database is empty for this test
        # (Though fixtures usually handle this)
        response = client.get("/api/suppliers/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_suppliers_with_data(self, client, test_db: Session):
        """Test getting suppliers list."""
        repo = SuppliersRepository(test_db)
        repo.add(name='Test Supplier', email='test@supplier.com', phone='555-1234')
        
        response = client.get("/api/suppliers/")
        assert response.status_code == 200
        
        suppliers = response.json()
        assert len(suppliers) >= 1
        assert any(s['name'] == 'Test Supplier' for s in suppliers)
    
    def test_get_suppliers_with_search(self, client, test_db: Session):
        """Test searching suppliers."""
        repo = SuppliersRepository(test_db)
        repo.add(name='Quality Foods Inc', email='quality@foods.com', phone='555-0001')
        repo.add(name='Premium Supplies', email='premium@supplies.com', phone='555-0002')
        repo.add(name='Quick Delivery Corp', email='quick@delivery.com', phone='555-0003')
        
        response = client.get("/api/suppliers/?search=quality")
        assert response.status_code == 200
        
        suppliers = response.json()
        assert len(suppliers) >= 1
        for supplier in suppliers:
            assert 'quality' in supplier['name'].lower()
    
    def test_get_new_supplier_form(self, client):
        """Test getting new supplier form."""
        response = client.get("/api/suppliers/new")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
    
    def test_get_edit_supplier_form_existing(self, client, test_db: Session):
        """Test getting edit form for existing supplier."""
        repo = SuppliersRepository(test_db)
        repo.add(name='Edit Test', email='edit@test.com', phone='555-5555')
        
        supplier = repo.by_name('Edit Test')
        response = client.get(f"/api/suppliers/{supplier.id}/edit")
        assert response.status_code == 200
    
    def test_get_edit_supplier_form_non_existing(self, client):
        """Test getting edit form for non-existent supplier."""
        response = client.get("/api/suppliers/99999/edit")
        assert response.status_code == 404
