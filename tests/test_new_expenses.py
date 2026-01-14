import pytest
from tests.core import model, conn, SQLiteModel

class TestExpenseDocuments:
    
    def test_create_expense_type(self, model: SQLiteModel):
        """Test creating an expense type."""
        # Ensure category exists first (Utils initialized with defaults)
        categories = model.utils().get_expense_category_names()
        assert "Materials" in categories
        
        model.expense_types().add(
            name="Test Flour",
            default_price=50.0,
            category_name="Materials",
            stock=True
        )
        
        types = model.expense_types().data()
        assert len(types) >= 1
        t = [x for x in types if x.name == "Test Flour"][0]
        assert t.default_price == 50.0
        assert t.stock is True

    def test_create_expense_document_simple(self, model: SQLiteModel):
        """Test creating a simple expense document."""
        # Setup: Create Expense Type
        model.expense_types().add("Service Fee", 100.0, "Utilities", False)
        # Get ID
        et_data = model.expense_types().data()
        et = next(x for x in et_data if x.name == "Service Fee")
        
        # Create Document items
        # We need unit ID. 'pc' is likely ID 4 or we queries it.
        # Ideally we should use a helper or repo to get unit id, but direct SQL is also fine in tests or utils
        # Let's rely on what we know or query it safely.
        # Since 'pc' is in INITIAL_UNITS, it should be there.
        # We can use a property of the model if we exposed it, or just use the DB connection since model has it.
        cursor = model._conn.cursor()
        cursor.execute("SELECT id FROM units WHERE name='pc'")
        row = cursor.fetchone()
        assert row is not None, "Unit 'pc' not found"
        unit_id = row[0]
        
        items = [{
            'expense_type_id': et.id,
            'quantity': 2.0,
            'price_per_unit': 100.0,
            'unit_id': unit_id
        }]
        
        # Add Supplier
        model.suppliers().add(name="Utility Co")
        supplier = model.suppliers().by_name("Utility Co")
        
        # Add Document
        doc_id = model.expense_documents().add(
            date="2024-01-01 10:00",
            supplier_id=supplier.id,
            total_amount=200.0,
            comment="Test Service",
            items=items
        )
        
        assert doc_id is not None
        
        # Verify Document
        docs = model.expense_documents().get_documents_with_details()
        assert len(docs) == 1
        assert docs[0]['total_amount'] == 200.0
        assert docs[0]['supplier_name'] == "Utility Co"
        
        # Verify Items
        doc_items = model.expense_documents().get_document_items(doc_id)
        assert len(doc_items) == 1
        assert doc_items[0]['total_price'] == 200.0
        assert doc_items[0]['expense_type_name'] == "Service Fee"

    def test_expense_updates_stock(self, model: SQLiteModel):
        """Test that expense marked as 'stock' updates inventory."""
        # Setup
        model.expense_types().add("Flour", 20.0, "Materials", True)
        et = next(x for x in model.expense_types().data() if x.name == "Flour")
        
        cursor = model._conn.cursor()
        cursor.execute("SELECT id FROM units WHERE name='kg'")
        row = cursor.fetchone()
        assert row is not None
        unit_id = row[0]
        
        # 1. Create Expense Document
        items = [{
            'expense_type_id': et.id,
            'quantity': 10.0,
            'price_per_unit': 20.0,
            'unit_id': unit_id
        }]
        
        model.suppliers().add(name="Flour Suppl")
        sid = model.suppliers().by_name("Flour Suppl").id
        
        model.expense_documents().add("2024-01-01", sid, 200.0, "", items)
        
        # 2. Check Stock
        stock_items = model.stock().data()
        # Should automatically create a stock item named "Flour"
        assert len(stock_items) == 1
        assert stock_items[0].name == "Flour"
        assert stock_items[0].quantity == 10.0
        
        # 3. Add another expense for same item
        items2 = [{
            'expense_type_id': et.id,
            'quantity': 5.0,
            'price_per_unit': 22.0,
            'unit_id': unit_id
        }]
        model.expense_documents().add("2024-01-02", sid, 110.0, "", items2)
        
        # 4. Check Stock again
        stock_items = model.stock().data()
        assert stock_items[0].quantity == 15.0 # 10 + 5

    def test_calculate_expenses_total(self, model: SQLiteModel):
        """Test that model.calculate_expenses() uses the new table."""
        # Init
        cursor = model._conn.cursor()
        cursor.execute("SELECT id FROM units WHERE name='pc'")
        unit_id = cursor.fetchone()[0]
        
        model.expense_types().add("T1", 10.0, "Other", False)
        et = next(x for x in model.expense_types().data() if x.name == "T1")
        
        model.suppliers().add(name="S1")
        sid = model.suppliers().by_name("S1").id
        
        # Add Doc 1: Total 100
        model.expense_documents().add("2024-01-01", sid, 100.0, "", [{
            'expense_type_id': et.id, 'quantity': 10, 'price_per_unit': 10, 'unit_id': unit_id
        }])
        
        # Add Doc 2: Total 50.50
        model.expense_documents().add("2024-01-02", sid, 50.50, "", [{
            'expense_type_id': et.id, 'quantity': 5, 'price_per_unit': 10.1, 'unit_id': unit_id
        }])
        
        total = model.calculate_expenses()
        assert total == 150.50
