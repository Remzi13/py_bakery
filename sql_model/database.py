"""SQLAlchemy database configuration and initialization."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session, scoped_session
from typing import Generator, Optional
from sqlalchemy import event

# Database URL
from api.utils import get_database_url
DATABASE_URL = get_database_url()

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)

# Declarative base for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_to_use=None):
    """Create all tables and populate reference data."""
    if engine_to_use is None:
        engine_to_use = engine
        db = SessionLocal()
    else:
        # Create a one-off session for initialization with the provided engine
        InitSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_to_use)
        db = InitSession()

    Base.metadata.create_all(bind=engine_to_use)
    
    # Populate reference data
    from sql_model.entities import Unit, StockCategory, ExpenseCategory, SystemSettings
    from api.version import DB_VERSION
    
    try:
        # Create default units
        default_units = ['kg', 'g', 'l', 'ml', 'pc']
        for unit_name in default_units:
            if not db.query(Unit).filter(Unit.name == unit_name).first():
                db.add(Unit(name=unit_name))
        
        # Create default stock categories
        default_stock_categories = ['Materials', 'Packaging', 'Equipment']
        for cat_name in default_stock_categories:
            if not db.query(StockCategory).filter(StockCategory.name == cat_name).first():
                db.add(StockCategory(name=cat_name))
        
        # Create default expense categories
        default_expense_categories = ['Materials', 'Equipment', 'Utilities', 'Inventory', 'Salary', 'Other']
        for cat_name in default_expense_categories:
            if not db.query(ExpenseCategory).filter(ExpenseCategory.name == cat_name).first():
                db.add(ExpenseCategory(name=cat_name))
        
        # Create default database version
        if not db.query(SystemSettings).filter(SystemSettings.key == 'db_version').first():
            db.add(SystemSettings(key='db_version', value=DB_VERSION))
            
        db.commit()
    finally:
        db.close()


def get_unit_by_name(db: Session, name: str) -> Optional[int]:
    """Get unit ID by name."""
    from sql_model.entities import Unit
    unit = db.query(Unit).filter(Unit.name == name).first()
    return unit.id if unit else None


def get_expense_category_by_name(db: Session, name: str) -> Optional[int]:
    """Get expense category ID by name."""
    from sql_model.entities import ExpenseCategory
    category = db.query(ExpenseCategory).filter(ExpenseCategory.name == name).first()
    return category.id if category else None


def close_db():
    """Close all sessions."""
    ScopedSession.remove()


# ============================================================================
# Test Helpers - Backward Compatibility for Tests
# ============================================================================

def create_connection(db_file: str = "bakery_management.db"):
    """
    Create a test database connection (SQLAlchemy Session).
    Returns a Session for in-memory or file-based database.
    """
    if db_file == ":memory:":
        db_url = "sqlite:///:memory:"
    else:
        db_url = f"sqlite:///{db_file}"
    
    test_engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Enable foreign keys
    @event.listens_for(test_engine, "connect")
    def set_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSession()
    session._test_engine = test_engine  # Store for cleanup
    return session


def initialize_db(db_session: Session):
    """
    Initialize test database with tables and reference data.
    Works with a SQLAlchemy Session.
    """
    engine_to_use = db_session.get_bind()
    
    # Create all tables
    Base.metadata.create_all(bind=engine_to_use)
    
    # Populate reference data
    from sql_model.entities import Unit, StockCategory, ExpenseCategory, SystemSettings
    from api.version import DB_VERSION
    
    try:
        # Create default units
        default_units = ['kg', 'g', 'l', 'ml', 'pc']
        for unit_name in default_units:
            if not db_session.query(Unit).filter(Unit.name == unit_name).first():
                db_session.add(Unit(name=unit_name))
        
        # Create default stock categories
        default_stock_categories = ['Materials', 'Packaging', 'Equipment']
        for cat_name in default_stock_categories:
            if not db_session.query(StockCategory).filter(StockCategory.name == cat_name).first():
                db_session.add(StockCategory(name=cat_name))
        
        # Create default expense categories
        default_expense_categories = ['Materials', 'Equipment', 'Utilities', 'Other']
        for cat_name in default_expense_categories:
            if not db_session.query(ExpenseCategory).filter(ExpenseCategory.name == cat_name).first():
                db_session.add(ExpenseCategory(name=cat_name))
        
        # Create default database version
        if not db_session.query(SystemSettings).filter(SystemSettings.key == 'db_version').first():
            db_session.add(SystemSettings(key='db_version', value=DB_VERSION))

        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e