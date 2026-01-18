"""Simple test to verify SQLAlchemy migration."""

import sys
sys.path.insert(0, '.')

from sql_model.model import SQLAlchemyModel

def test_basic_initialization():
    """Test basic model initialization."""
    try:
        model = SQLAlchemyModel()
        print("✓ Model initialized successfully")
        
        # Test basic access to repositories
        print(f"✓ Products repository: {model.products()}")
        print(f"✓ Stock repository: {model.stock()}")
        print(f"✓ Sales repository: {model.sales()}")
        
        model.close()
        print("✓ Model closed successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_initialization()
    sys.exit(0 if success else 1)
