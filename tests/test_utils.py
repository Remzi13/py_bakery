"""Tests for utils repository."""

import pytest
from sqlalchemy.orm import Session
from repositories.utils import UtilsRepository
from sql_model.entities import Unit, StockCategory, ExpenseCategory


class TestUtilsRepository:
    """Test UtilsRepository methods."""
    
    def test_get_unit_names(self, test_db: Session):
        """Test retrieving all unit names."""
        repo = UtilsRepository(test_db)
        
        names = repo.get_unit_names()
        assert len(names) >= 1
        assert 'kg' in names
        assert 'g' in names
    
    def test_get_stock_category_names(self, test_db: Session):
        """Test retrieving all stock category names."""
        repo = UtilsRepository(test_db)
        
        names = repo.get_stock_category_names()
        assert len(names) >= 1
        assert 'Materials' in names
        assert 'Packaging' in names
    
    def test_get_expense_category_names(self, test_db: Session):
        """Test retrieving all expense category names."""
        repo = UtilsRepository(test_db)
        
        names = repo.get_expense_category_names()
        assert len(names) >= 1
        assert 'Materials' in names
        assert 'Equipment' in names
    
    def test_get_unit_name_by_id(self, test_db: Session):
        """Test retrieving unit name by ID."""
        repo = UtilsRepository(test_db)
        
        # Get a unit ID first
        units = test_db.query(Unit).all()
        assert len(units) > 0
        
        unit = units[0]
        name = repo.get_unit_name_by_id(unit.id)
        
        assert name is not None
        assert name == unit.name
    
    def test_get_unit_name_by_invalid_id(self, test_db: Session):
        """Test retrieving unit with invalid ID."""
        repo = UtilsRepository(test_db)
        
        name = repo.get_unit_name_by_id(99999)
        assert name is None
    
    def test_get_stock_category_name_by_id(self, test_db: Session):
        """Test retrieving stock category name by ID."""
        repo = UtilsRepository(test_db)
        
        # Get a category ID first
        categories = test_db.query(StockCategory).all()
        assert len(categories) > 0
        
        category = categories[0]
        name = repo.get_stock_category_name_by_id(category.id)
        
        assert name is not None
        assert name == category.name
    
    def test_get_stock_category_name_by_invalid_id(self, test_db: Session):
        """Test retrieving stock category with invalid ID."""
        repo = UtilsRepository(test_db)
        
        name = repo.get_stock_category_name_by_id(99999)
        assert name is None
    
    def test_get_expense_category_name_by_id(self, test_db: Session):
        """Test retrieving expense category name by ID."""
        repo = UtilsRepository(test_db)
        
        # Get a category ID first
        categories = test_db.query(ExpenseCategory).all()
        assert len(categories) > 0
        
        category = categories[0]
        name = repo.get_expense_category_name_by_id(category.id)
        
        assert name is not None
        assert name == category.name
    
    def test_get_expense_category_name_by_invalid_id(self, test_db: Session):
        """Test retrieving expense category with invalid ID."""
        repo = UtilsRepository(test_db)
        
        name = repo.get_expense_category_name_by_id(99999)
        assert name is None
    
    def test_get_expense_category_id_by_name(self, test_db: Session):
        """Test retrieving expense category ID by name."""
        repo = UtilsRepository(test_db)
        
        category_id = repo.get_expense_category_id_by_name('Materials')
        assert category_id is not None
        
        # Verify by retrieving the category
        category = test_db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id).first()
        assert category is not None
        assert category.name == 'Materials'
    
    def test_get_expense_category_id_by_invalid_name(self, test_db: Session):
        """Test retrieving expense category with invalid name."""
        repo = UtilsRepository(test_db)
        
        category_id = repo.get_expense_category_id_by_name('NonExistentCategory')
        assert category_id is None
