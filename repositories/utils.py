from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from sql_model.entities import Unit, StockCategory, ExpenseCategory


class UtilsRepository:
    """Repository for access to reference tables (Units, Categories)."""

    def __init__(self, db: Session):
        self.db = db


    def get_units(self) -> List[Unit]:
        return self.db.query(Unit).all()

    def get_all_units(self) -> List[Dict[str, Any]]:
        """Return all units as a list of dictionaries with id and name."""
        units = self.db.query(Unit).all()
        return [{"id": u.id, "name": u.name} for u in units]

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

    def get_conversion_factor_by_unit_id(self, unit_id_a: int, unit_id_b: int) -> Optional[float]:
        """Convert unit ID to its conversion factor. 
        Amount in unit_a * conversion_factor = Amount in unit_b."""
        unit_a = self.db.query(Unit).filter(Unit.id == unit_id_a).first()
        unit_b = self.db.query(Unit).filter(Unit.id == unit_id_b).first()
        if not unit_a or not unit_b:
            return 1.0
        if unit_a.id == unit_b.id:
            return 1.0
        
        # Mapping: (from_unit, to_unit) -> factor
        conversions = {
            ("g", "kg"): 0.001,
            ("kg", "g"): 1000.0,
            ("ml", "l"): 0.001,
            ("l", "ml"): 1000.0,
        }
        
        return conversions.get((unit_a.name, unit_b.name), 1.0)
    
    
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
        