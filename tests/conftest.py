"""Pytest configuration and fixtures for bakery management system."""

import pytest
import os
import sys
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from sql_model.database import Base, get_db
from sql_model.entities import Unit, StockCategory, ExpenseCategory


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session with all tables and reference data."""
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
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
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
