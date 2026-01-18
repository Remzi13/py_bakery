import pytest
from sqlalchemy.orm import Session

from sql_model.model import SQLiteModel
from sql_model.database import create_connection, initialize_db, get_unit_by_name
from sql_model.entities import ExpenseCategory, StockCategory, Unit

TEST_DB = ':memory:'

@pytest.fixture
def conn() -> Session:
    """Provides a clean, initialized in-memory database session for testing."""
    session = create_connection(TEST_DB)
    initialize_db(session)
    yield session
    session.close()


@pytest.fixture
def model() -> SQLiteModel:
    """Provides a SQLiteModel instance for testing."""
    return SQLiteModel()


# Helper functions for tests
def get_category_id_by_name(db: Session, table_class, name: str):
    """Get category ID by name from database."""
    obj = db.query(table_class).filter(table_class.name == name).first()
    return obj.id if obj else None
