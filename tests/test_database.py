"""Database and models integration tests."""

import pytest
from sqlalchemy.orm import Session
from sql_model.entities import Product, StockItem, StockCategory, Unit


class TestDatabaseIntegration:
    """Test database and model integration."""
    
    def test_database_initialization(self, test_db: Session):
        """Test that database is properly initialized."""
        # Check that reference data exists
        units = test_db.query(Unit).all()
        assert len(units) >= 4
        
        categories = test_db.query(StockCategory).all()
        assert len(categories) >= 3
    
    def test_units_exist(self, test_db: Session):
        """Test that default units are created."""
        unit_names = [u.name for u in test_db.query(Unit).all()]
        
        assert 'kg' in unit_names
        assert 'g' in unit_names
        assert 'l' in unit_names
        assert 'pc' in unit_names
    
    def test_stock_categories_exist(self, test_db: Session):
        """Test that default stock categories are created."""
        category_names = [c.name for c in test_db.query(StockCategory).all()]
        
        assert 'Materials' in category_names
        assert 'Packaging' in category_names
        assert 'Equipment' in category_names
    
    def test_create_product_entity(self, test_db: Session):
        """Test creating a Product entity."""
        product = Product(name='Test Product', price=100)
        test_db.add(product)
        test_db.commit()
        
        retrieved = test_db.query(Product).filter(Product.name == 'Test Product').first()
        assert retrieved is not None
        assert retrieved.price == 100
    
    def test_create_stock_item_entity(self, test_db: Session):
        """Test creating a StockItem entity."""
        unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
        category = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
        
        item = StockItem(
            name='Test Material',
            category_id=category.id,
            quantity=50.0,
            unit_id=unit.id
        )
        test_db.add(item)
        test_db.commit()
        
        retrieved = test_db.query(StockItem).filter(StockItem.name == 'Test Material').first()
        assert retrieved is not None
        assert retrieved.quantity == 50.0
        assert retrieved.category_id == category.id
    
    def test_relationships(self, test_db: Session):
        """Test entity relationships."""
        unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
        category = test_db.query(StockCategory).filter(StockCategory.name == 'Materials').first()
        
        # Create stock items
        item = StockItem(
            name='Relationship Test',
            category_id=category.id,
            quantity=10.0,
            unit_id=unit.id
        )
        test_db.add(item)
        test_db.commit()
        
        # Verify relationships
        retrieved_item = test_db.query(StockItem).filter(StockItem.name == 'Relationship Test').first()
        assert retrieved_item.unit_id == unit.id
        assert retrieved_item.category_id == category.id
