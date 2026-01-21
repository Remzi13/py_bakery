"""Pytest configuration and fixtures for bakery management system."""

import pytest
import os
import sys

# Define database URL for tests before any imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from unittest.mock import patch

# Mock init_db globally for the entire test session to prevent it from running during tests
# We do our own initialization in the test_db fixture
init_db_patcher = patch('sql_model.database.init_db')
init_db_patcher.start()

from main import app
from api.dependencies import get_db, get_model
from sql_model.database import Base
from sql_model.entities import Unit, StockCategory, ExpenseCategory
from sql_model.model import SQLAlchemyModel


@pytest.fixture(scope="function")
def model(test_db):
    """Create a model instance with the test database session."""
    return SQLAlchemyModel(db=test_db)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session in memory with all tables and reference data."""
    from sqlalchemy import create_engine, event
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker
    
    # Use StaticPool to keep the memory database alive between connections
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()
    
    # Populate reference data
    default_units = ['kg', 'g', 'l', 'pc']
    for unit_name in default_units:
        session.add(Unit(name=unit_name))
    
    default_stock_categories = ['Materials', 'Packaging', 'Equipment']
    for cat_name in default_stock_categories:
        session.add(StockCategory(name=cat_name))
    
    default_expense_categories = ['Materials', 'Equipment', 'Utilities', 'Other']
    for cat_name in default_expense_categories:
        session.add(ExpenseCategory(name=cat_name))
    
    session.commit()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database dependency."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
            
    def override_get_model():
        model = SQLAlchemyModel(db=test_db)
        try:
            yield model
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_model] = override_get_model
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
