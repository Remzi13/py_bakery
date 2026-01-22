from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from sql_model.entities import Unit, StockCategory, ExpenseCategory


class UtilsRepository:
    """Repository for access to reference tables (Units, Categories)."""

    def __init__(self, db: Session):
        self.db = db


    def get_units(self) -> List[Unit]:
        return self.db.query(Unit).all()

    def get_unit_names(self) -> List[str]:
        """Return list of all unit names (e.g., ['kg', 'g'])."""
        return [unit.name for unit in self.db.query(Unit).order_by(Unit.id).all()]

    def get_stock_category_names(self) -> List[str]:
        """Return list of all stock category names."""
        return [cat.name for cat in self.db.query(StockCategory).order_by(StockCategory.id).all()]

    def get_expense_category_names(self) -> List[str]:
        """Return list of all expense category names."""
        return [cat.name for cat in self.db.query(ExpenseCategory).order_by(ExpenseCategory.id).all()]
    
    def get_unit_name_by_id(self, unit_id: int) -> Optional[str]:
        """Convert unit ID to its string name."""
        unit = self.db.query(Unit).filter(Unit.id == unit_id).first()
        return unit.name if unit else None
    
    def get_stock_category_name_by_id(self, category_id: int) -> Optional[str]:
        """Convert stock category ID to its string name."""
        category = self.db.query(StockCategory).filter(StockCategory.id == category_id).first()
        return category.name if category else None

    def get_expense_category_name_by_id(self, category_id: int) -> Optional[str]:
        """Convert expense category ID to its string name."""
        category = self.db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id).first()
        return category.name if category else None
    
    def get_expense_category_id_by_name(self, name: str) -> Optional[int]:
        """
        Return expense category ID by its string name (e.g., 'Materials').
        
        Args:
            name: String name of category
            
        Returns:
            Category ID or None if not found
        """
        category = self.db.query(ExpenseCategory).filter(ExpenseCategory.name == name).first()
        return category.id if category else None 
        