"""Simplified comprehensive tests for bakery management system using pytest."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sql_model.model import SQLAlchemyModel
from repositories.products import ProductsRepository
from repositories.suppliers import SuppliersRepository
from repositories.utils import UtilsRepository


@pytest.fixture
def model(test_db: Session):
    """Create a test model instance with database session."""
    from sql_model.database import init_db
    # Initialize database with reference data
    init_db()
    
    model_instance = SQLAlchemyModel()
    model_instance.db = test_db
    
    # Reinitialize repositories with test database
    model_instance._products_repo = ProductsRepository(test_db)
    model_instance._suppliers_repo = SuppliersRepository(test_db)
    model_instance._utils_repo = UtilsRepository(test_db)
    
    yield model_instance
    model_instance.close()


class TestProductRepositoryIntegration:
    """Integration tests for products using the model."""
    
    def test_create_and_retrieve_product(self, model):
        """Test creating and retrieving a product."""
        # Add a product
        model._products_repo.add('Test Bread', 150, [])
        
        # Retrieve it
        product = model._products_repo.by_name('Test Bread')
        assert product is not None
        assert product.name == 'Test Bread'
        assert product.price == 150


class TestSuppliersRepositoryIntegration:
    """Integration tests for suppliers."""
    
    def test_supplier_operations(self, model):
        """Test supplier CRUD operations."""
        # Create
        model._suppliers_repo.add('Test Supplier', 'test@supplier.com', '555-1234')
        
        # Retrieve
        supplier = model._suppliers_repo.by_name('Test Supplier')
        assert supplier is not None
        assert supplier.email == 'test@supplier.com'
        
        # Update
        model._suppliers_repo.update(supplier.id, name='Updated Supplier')
        
        # Verify update
        updated = model._suppliers_repo.by_id(supplier.id)
        assert updated.name == 'Updated Supplier'


class TestUtilsRepository:
    """Tests for utility/reference data repository."""
    
    def test_get_reference_data(self, model):
        """Test retrieving reference data."""
        # Units
        units = model._utils_repo.get_unit_names()
        assert 'kg' in units
        
        # Stock categories
        stock_cats = model._utils_repo.get_stock_category_names()
        assert 'Materials' in stock_cats
        
        # Expense categories
        exp_cats = model._utils_repo.get_expense_category_names()
        assert 'Materials' in exp_cats
    
    def test_id_to_name_conversion(self, model):
        """Test converting IDs to names and vice versa."""
        # Get an ID and convert to name
        units = model.db.query(__import__('sql_model.entities', fromlist=['Unit']).Unit).all()
        if units:
            unit = units[0]
            name = model._utils_repo.get_unit_name_by_id(unit.id)
            assert name == unit.name
