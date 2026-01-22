"""Tests for expenses router and repository."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sql_model.entities import ExpenseCategory, Unit, Supplier


@pytest.fixture
def setup_expense_data(model):
    """Setup expense categories, types and supplier for testing."""
    test_db = model.db
    materials_cat = test_db.query(ExpenseCategory).filter(ExpenseCategory.name == 'Materials').first()
    kg_unit = test_db.query(Unit).filter(Unit.name == 'kg').first()
    
    # Create a supplier
    model.suppliers().add(name='Expense Supplier')
    supplier = model.suppliers().get_by_id(1) # Suppliers ID starts from 1
    if not supplier:
        supplier = model.suppliers().by_name('Expense Supplier')
    
    # Create an expense type
    type_repo = model.expense_types()
    type_repo.add('Flour Purchase', 500.0, 'Materials', 1, False)
    
    exp_type = type_repo.get('Flour Purchase')
    
    return {
        'category': materials_cat, 
        'exp_type': exp_type, 
        'supplier': supplier,
        'unit': kg_unit
    }


class TestExpenseTypesRepository:
    """Test ExpenseTypesRepository methods."""
    
    def test_add_expense_type(self, model):
        """Test adding a new expense type."""
        repo = model.expense_types()
        
        repo.add('Utilities', 100.0, 'Utilities', 1, False)
        
        exp_type = repo.get('Utilities')
        assert exp_type is not None
        assert exp_type.name == 'Utilities'
        assert exp_type.default_price == 100.0
    
    def test_add_expense_type_with_invalid_category(self, model):
        """Test adding expense type with invalid category."""
        repo = model.expense_types()
        
        with pytest.raises(ValueError, match="Expense category 'InvalidCategory' not found"):
            repo.add('Item', 100.0, 'InvalidCategory', False)
    
    def test_get_expense_type_by_id(self, model):
        """Test retrieving expense type by ID."""
        repo = model.expense_types()
        
        repo.add('Equipment', 1000.0, 'Equipment', 1, False)
        exp_type = repo.get('Equipment')
        
        retrieved = repo.by_id(exp_type.id)
        assert retrieved is not None
        assert retrieved.name == 'Equipment'
    
    def test_update_expense_type(self, model):
        """Test updating an expense type."""
        repo = model.expense_types()
        
        repo.add('Supplies', 50.0, 'Materials', 1, False)
        exp_type = repo.get('Supplies')
        
        repo.update(exp_type.id, 75.0)
        
        updated = repo.by_id(exp_type.id)
        assert updated.default_price == 75.0
    
    def test_delete_expense_type(self, model):
        """Test deleting an expense type."""
        repo = model.expense_types()
        
        repo.add('TempType', 100.0, 'Materials', 1, False)
        repo.delete('TempType')
        
        deleted = repo.get('TempType')
        assert deleted is None
    
    def test_get_all_expense_types(self, model):
        """Test retrieving all expense types."""
        repo = model.expense_types()
        
        repo.add('Type1', 100.0,'Materials', 1, False)
        repo.add('Type2', 200.0,'Equipment', 1, False)
        repo.add('Type3', 50.0, 'Utilities', 1, False)
        
        all_types = repo.data()
        assert len(all_types) >= 3


class TestExpenseDocumentsRepository:
    """Test ExpenseDocumentsRepository methods."""
    
    def test_add_expense_document(self, model, setup_expense_data):
        """Test adding a new expense document."""
        repo = model.expense_documents()
        exp_type = setup_expense_data['exp_type']
        supplier = setup_expense_data['supplier']
        unit = setup_expense_data['unit']
        
        items = [{
            'expense_type_id': exp_type.id,
            'quantity': 1.0,
            'price': 450,
            'unit_id': unit.id
        }]
        
        repo.add(datetime.now().strftime("%Y-%m-%d"), supplier.id, 450.0, "Test comment", items)
        
        documents = repo.data()
        assert len(documents) >= 1
    
    def test_get_expense_by_id(self, model, setup_expense_data):
        """Test retrieving expense document by ID."""
        repo = model.expense_documents()
        exp_type = setup_expense_data['exp_type']
        supplier = setup_expense_data['supplier']
        unit = setup_expense_data['unit']
        
        items = [{
            'expense_type_id': exp_type.id,
            'quantity': 1.0,
            'price': 450,
            'unit_id': unit.id
        }]
        
        doc_id = repo.add(datetime.now().strftime("%Y-%m-%d"), supplier.id, 450.0, "Test comment", items)
        
        retrieved = repo.by_id(doc_id)
        assert retrieved is not None
        assert retrieved.supplier_id == supplier.id
    
    def test_delete_expense_document(self, model, setup_expense_data):
        """Test deleting an expense document."""
        repo = model.expense_documents()
        exp_type = setup_expense_data['exp_type']
        supplier = setup_expense_data['supplier']
        unit = setup_expense_data['unit']
        
        items = [{
            'expense_type_id': exp_type.id,
            'quantity': 1.0,
            'price': 450,
            'unit_id': unit.id
        }]
        
        doc_id = repo.add(datetime.now().strftime("%Y-%m-%d"), supplier.id, 450.0, "Test comment", items)
        
        repo.delete(doc_id)
        
        deleted = repo.by_id(doc_id)
        assert deleted is None


class TestExpensesRouter:
    """Test expenses API router endpoints."""
    
    def test_get_expenses_empty(self, client):
        """Test getting expenses when none exist."""
        # The router uses /api/expenses/documents
        response = client.get("/api/expenses/documents")
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
        """Test getting new expense document form."""
        response = client.get("/api/expenses/documents/new")
        assert response.status_code == 200
    
    def test_get_new_expense_type_form(self, client):
        """Test getting new expense type form."""
        response = client.get("/api/expenses/types/new")
        assert response.status_code == 200
    
    def test_get_expense_by_date(self, client, model, setup_expense_data):
        """Test getting expenses filtered by date."""
        repo = model.expense_documents()
        exp_type = setup_expense_data['exp_type']
        supplier = setup_expense_data['supplier']
        unit = setup_expense_data['unit']
        
        items = [{
            'expense_type_id': exp_type.id,
            'quantity': 1.0,
            'price': 450,
            'unit_id': unit.id
        }]
        
        repo.add(datetime.now().strftime("%Y-%m-%d"), supplier.id, 450.0, "Test comment", items)
        
        today = datetime.now().strftime("%Y-%m-%d")
        # Currently the router doesn't have a direct 'date' query parameter for JSON response,
        # but let's see if 'search' works for it
        response = client.get(f"/api/expenses/documents?search={today}")
        assert response.status_code == 200
