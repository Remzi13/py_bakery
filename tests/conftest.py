"""Pytest configuration and fixtures for bakery management system."""

import pytest
import os
import sys

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
# Disable automatic database initialization in lifespan for tests
app.state.skip_init_db = True
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
    
    # Use the application's init_db to setup the tables and data
    from sql_model.database import init_db
    init_db(engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()
    
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
