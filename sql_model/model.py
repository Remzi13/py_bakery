"""SQLAlchemy-based Model for managing the bakery."""

from sqlalchemy.orm import Session
from sql_model.database import SessionLocal, init_db

from repositories.products import ProductsRepository
from repositories.stock import StockRepository
from repositories.sales import SalesRepository
from repositories.expense_types import ExpenseTypesRepository
from repositories.write_offs import WriteOffsRepository
from repositories.suppliers import SuppliersRepository
from repositories.orders import OrdersRepository
from repositories.utils import UtilsRepository
from repositories.expense_documents import ExpenseDocumentsRepository


class SQLAlchemyModel:
    """
    Class for managing the bakery using SQLAlchemy ORM.
    Encapsulates sessions and provides access to repositories.
    """

    def __init__(self, db: Session = None):
        """
        Initializes the SQLAlchemy Model.
        Creates database tables if they don't exist.
        """
        # Create session
        if db:
            self.db = db
        else:
            self.db: Session = SessionLocal()
        
        # Initialize repositories
        self._stock_repo = StockRepository(self.db, self)
        self._expense_types_repo = ExpenseTypesRepository(self.db)
        self._products_repo = ProductsRepository(self.db)
        self._sales_repo = SalesRepository(self.db, self)
        self._utils_repo = UtilsRepository(self.db)
        self._write_offs_repo = WriteOffsRepository(self.db, self)
        self._suppliers_repo = SuppliersRepository(self.db)
        self._orders_repo = OrdersRepository(self.db, self)
        self._expense_documents_repo = ExpenseDocumentsRepository(self.db, self)

    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()

    # --- Methods that return repositories ---

    def utils(self) -> UtilsRepository:
        return self._utils_repo

    def products(self) -> ProductsRepository:
        return self._products_repo

    def stock(self) -> StockRepository:
        return self._stock_repo

    def sales(self) -> SalesRepository:
        return self._sales_repo

    def expense_types(self) -> ExpenseTypesRepository:
        return self._expense_types_repo

    def writeoffs(self) -> WriteOffsRepository:
        return self._write_offs_repo

    def suppliers(self) -> SuppliersRepository:
        return self._suppliers_repo

    def orders(self) -> OrdersRepository:
        return self._orders_repo

    def expense_documents(self) -> ExpenseDocumentsRepository:
        return self._expense_documents_repo

    # --- Business logic (calculations) ---

    def calculate_income(self) -> float:
        """Calculate total income from sales."""
        from sql_model.entities import Sale
        from sqlalchemy import func, Float
        
        result = self.db.query(
            func.sum(Sale.price * Sale.quantity * (1 - func.cast(Sale.discount, Float) / 100))
        ).scalar()
        return float(result) if result is not None else 0.0

    def calculate_expenses(self) -> float:
        """Calculate total expenses."""
        from sql_model.entities import ExpenseDocument
        from sqlalchemy import func
        
        result = self.db.query(func.sum(ExpenseDocument.total_amount)).scalar()
        return float(result) if result is not None else 0.0

    def calculate_profit(self) -> float:
        """Calculate profit."""
        return self.calculate_income() - self.calculate_expenses()


# Backward compatibility alias
SQLiteModel = SQLAlchemyModel