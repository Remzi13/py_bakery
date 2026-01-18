"""Tests for expenses router and repository."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.expense_types import ExpenseTypesRepository
from repositories.expense_documents import ExpenseDocumentsRepository
from sql_model.entities import ExpenseCategory, Unit


@pytest.fixture
def setup_expense_data(test_db: Session):
    """Setup expense categories and types for testing."""
    materials_cat = test_db.query(ExpenseCategory).filter(ExpenseCategory.name == 'Materials').first()
    
    # Create an expense type
    type_repo = ExpenseTypesRepository(test_db)
    type_repo.add('Flour Purchase', 500.0, 'Materials', False)
    
    exp_type = type_repo.get_by_name('Flour Purchase')
    
    return {'category': materials_cat, 'exp_type': exp_type}


class TestExpenseTypesRepository:
    """Test ExpenseTypesRepository methods."""
    
    def test_add_expense_type(self, test_db: Session):
        """Test adding a new expense type."""
        repo = ExpenseTypesRepository(test_db)
        
        repo.add('Utilities', 100.0, 'Utilities', False)
        
        exp_type = repo.get_by_name('Utilities')
        assert exp_type is not None
        assert exp_type.name == 'Utilities'
        assert exp_type.default_price == 100.0
    
    def test_add_expense_type_with_invalid_category(self, test_db: Session):
        """Test adding expense type with invalid category."""
        repo = ExpenseTypesRepository(test_db)
        
        with pytest.raises(ValueError, match="Category 'InvalidCategory' not found"):
            repo.add('Item', 100.0, 'InvalidCategory', False)
    
    def test_get_expense_type_by_id(self, test_db: Session):
        """Test retrieving expense type by ID."""
        repo = ExpenseTypesRepository(test_db)
        
        repo.add('Equipment', 1000.0, 'Equipment', False)
        exp_type = repo.get_by_name('Equipment')
        
        retrieved = repo.by_id(exp_type.id)
        assert retrieved is not None
        assert retrieved.name == 'Equipment'
    
    def test_update_expense_type(self, test_db: Session):
        """Test updating an expense type."""
        repo = ExpenseTypesRepository(test_db)
        
        repo.add('Supplies', 50.0, 'Materials', False)
        exp_type = repo.get_by_name('Supplies')
        
        repo.update(exp_type.id, 75.0)
        
        updated = repo.by_id(exp_type.id)
        assert updated.default_price == 75.0
    
    def test_delete_expense_type(self, test_db: Session):
        """Test deleting an expense type."""
        repo = ExpenseTypesRepository(test_db)
        
        repo.add('TempType', 100.0, 'Materials', False)
        exp_type = repo.get_by_name('TempType')
        type_id = exp_type.id
        
        repo.delete(type_id)
        
        deleted = repo.by_id(type_id)
        assert deleted is None
    
    def test_get_all_expense_types(self, test_db: Session):
        """Test retrieving all expense types."""
        repo = ExpenseTypesRepository(test_db)
        
        repo.add('Type1', 100.0, 'Materials', False)
        repo.add('Type2', 200.0, 'Equipment', False)
        repo.add('Type3', 50.0, 'Utilities', False)
        
        all_types = repo.data()
        assert len(all_types) >= 3


class TestExpenseDocumentsRepository:
    """Test ExpenseDocumentsRepository methods."""
    
    def test_add_expense_document(self, test_db: Session, setup_expense_data):
        """Test adding a new expense document."""
        repo = ExpenseDocumentsRepository(test_db)
        exp_type = setup_expense_data['exp_type']
        
        repo.add(exp_type.id, 450.0, 1.0)
        
        documents = repo.data()
        assert len(documents) >= 1
    
    def test_get_expense_by_id(self, test_db: Session, setup_expense_data):
        """Test retrieving expense document by ID."""
        repo = ExpenseDocumentsRepository(test_db)
        exp_type = setup_expense_data['exp_type']
        
        repo.add(exp_type.id, 450.0, 1.0)
        doc = repo.data()[0]
        
        retrieved = repo.by_id(doc.id)
        assert retrieved is not None
        assert retrieved.type_id == exp_type.id
    
    def test_delete_expense_document(self, test_db: Session, setup_expense_data):
        """Test deleting an expense document."""
        repo = ExpenseDocumentsRepository(test_db)
        exp_type = setup_expense_data['exp_type']
        
        repo.add(exp_type.id, 450.0, 1.0)
        doc = repo.data()[0]
        doc_id = doc.id
        
        repo.delete(doc_id)
        
        deleted = repo.by_id(doc_id)
        assert deleted is None
    
    def test_get_all_expenses(self, test_db: Session, setup_expense_data):
        """Test retrieving all expense documents."""
        repo = ExpenseDocumentsRepository(test_db)
        exp_type = setup_expense_data['exp_type']
        
        repo.add(exp_type.id, 450.0, 1.0)
        repo.add(exp_type.id, 500.0, 2.0)
        repo.add(exp_type.id, 400.0, 1.5)
        
        all_expenses = repo.data()
        assert len(all_expenses) >= 3


class TestExpensesRouter:
    """Test expenses API router endpoints."""
    
    def test_get_expenses_empty(self, client):
        """Test getting expenses when none exist."""
        response = client.get("/api/expenses/")
        assert response.status_code == 200
    
    def test_get_expense_types_empty(self, client):
        """Test getting expense types when none exist."""
        response = client.get("/api/expenses/types")
        assert response.status_code == 200
    
    def test_get_expense_categories(self, client):
        """Test getting expense categories."""
        response = client.get("/api/expenses/categories")
        assert response.status_code == 200
        
        categories = response.json()
        assert len(categories) >= 1
        assert 'Materials' in categories
    
    def test_get_new_expense_form(self, client):
        """Test getting new expense form."""
        response = client.get("/api/expenses/new")
        assert response.status_code == 200
    
    def test_get_new_expense_type_form(self, client):
        """Test getting new expense type form."""
        response = client.get("/api/expenses/types/new")
        assert response.status_code == 200
    
    def test_get_expense_by_date(self, client, test_db: Session, setup_expense_data):
        """Test getting expenses filtered by date."""
        repo = ExpenseDocumentsRepository(test_db)
        exp_type = setup_expense_data['exp_type']
        repo.add(exp_type.id, 450.0, 1.0)
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"/api/expenses/?date={today}")
        assert response.status_code == 200
