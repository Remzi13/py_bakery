from typing import Optional, List
from sqlalchemy.orm import Session

from sql_model.entities import ExpenseType, ExpenseCategory


class ExpenseTypesRepository:
    """Repository for ExpenseType entities using SQLAlchemy ORM."""

    def __init__(self, db: Session):
        self.db = db

    # --- Helper methods ---

    def _get_category_id(self, category_name: str) -> Optional[int]:
        """Get category ID by name."""
        category = self.db.query(ExpenseCategory).filter(
            ExpenseCategory.name == category_name
        ).first()
        return category.id if category else None

    # --- CRUD Methods ---

    def add(self, name: str, default_price: int, category_name: str,  unit_id: int, stock: bool = False,):
        """Add a new expense type."""
        try:
            category_id = self._get_category_id(category_name)
            if category_id is None:
                raise ValueError(f"Expense category '{category_name}' not found.")
            
            expense_type = ExpenseType(
                name=name,
                default_price=default_price,
                category_id=category_id,
                unit_id=unit_id,
                stock=stock                
            )
            self.db.add(expense_type)
            self.db.commit()
            return expense_type.id
        except Exception as e:
            self.db.rollback()
            if 'UNIQUE' in str(e):
                existing = self.get(name)
                return existing.id if existing else None
            else:
                raise e

    def get(self, name: str) -> Optional[ExpenseType]:
        """Get expense type by name."""
        return self.db.query(ExpenseType).filter(ExpenseType.name == name).first()

    def by_id(self, type_id: int) -> Optional[ExpenseType]:
        """Get expense type by ID."""
        return self.db.query(ExpenseType).filter(ExpenseType.id == type_id).first()

    def update(self, type_id: int, default_price: float):
        """Update expense type default price."""
        exp_type = self.by_id(type_id)
        if exp_type:
            try:
                exp_type.default_price = default_price
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e

    def full_update(self, type_id: int, name: str, default_price: float, category_name: str, unit_id: int, stock: bool):
        """Update all fields of an expense type."""
        exp_type = self.by_id(type_id)
        if exp_type:
            try:
                category_id = self._get_category_id(category_name)
                if category_id is None:
                    raise ValueError(f"Expense category '{category_name}' not found.")
                
                exp_type.name = name
                exp_type.default_price = default_price
                exp_type.category_id = category_id
                exp_type.unit_id = unit_id
                exp_type.stock = stock
                self.db.commit()
                return exp_type
            except Exception as e:
                self.db.rollback()
                raise e
        return None

    def delete_by_id(self, type_id: int):
        """Delete expense type by ID."""
        exp_type = self.by_id(type_id)
        if exp_type:
            try:
                self.db.delete(exp_type)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e

    def delete(self, name: str):
        """
        Delete expense type by name.
        (Should only be used in conjunction with deleting Stock item)
        """
        expense_type = self.get(name)
        if expense_type:
            try:
                self.db.delete(expense_type)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
    def data(self) -> List[ExpenseType]:
        """Return list of all expense types."""
        return self.db.query(ExpenseType).all()

    def len(self) -> int:
        """Return count of expense types."""
        return self.db.query(ExpenseType).count()

    def empty(self) -> bool:
        """Check if repository is empty."""
        return self.len() == 0
    
    def get_names_by_category_name(self, category_name: str) -> List[str]:
        """
        Return list of expense type names for a given category.
        """
        category_id = self._get_category_id(category_name)
        if category_id is None:
            return []
        
        return [et.name for et in self.db.query(ExpenseType).filter(
            ExpenseType.category_id == category_id
        ).order_by(ExpenseType.name).all()]
    
    def get_by_category_name(self, category_name: str) -> List[ExpenseType]:
        """Return all ExpenseType objects for a given category."""
        category_id = self._get_category_id(category_name)
        if category_id is None:
            return []
        
        return self.db.query(ExpenseType).filter(
            ExpenseType.category_id == category_id
        ).order_by(ExpenseType.name).all()