from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from sql_model.entities import StockItem, StockCategory, Unit, ExpenseType


class StockRepository:

    def __init__(self, db: Session, model_instance: Any):
        self.db = db
        self._model = model_instance  # Reference to Model for accessing other repositories

    # --- Helper methods ---

    def _get_category_id(self, category_name: str) -> Optional[int]:
        """Get category ID by name."""
        category = self.db.query(StockCategory).filter(
            StockCategory.name == category_name
        ).first()
        return category.id if category else None


    # --- CRUD/Logic Methods ---

    def add(self, name: str, category_name: str, quantity: float, unit_name: str):
        """Add a new stock item to inventory."""
        try:
            # Get unit by name
            unit = self.db.query(Unit).filter(Unit.name == unit_name).first()
            if unit is None:
                raise ValueError(f"Unit '{unit_name}' not found.")
            
            category_id = self._get_category_id(category_name)
            if category_id is None:
                raise ValueError(f"Category '{category_name}' not found.")
            
            # Create new stock item
            stock_item = StockItem(
                name=name,
                category_id=category_id,
                quantity=quantity,
                unit_id=unit.id
            )
            self.db.add(stock_item)
            self.db.flush()
            
            # Also create expense type for this stock item
            self._model.expense_types().add(
                name=name,
                default_price=100,
                category_name="Materials",
                stock=True
            )
            self.db.commit()
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            if 'UNIQUE' in str(e):
                raise ValueError(f"Stock item with name '{name}' already exists.")
            raise e


    def get(self, name: str) -> Optional[StockItem]:
        """Get stock item by name."""
        return self.db.query(StockItem).filter(StockItem.name == name).first()

    def by_id(self, id: int) -> Optional[StockItem]:
        """Get stock item by ID."""
        return self.db.query(StockItem).filter(StockItem.id == id).first()
    
    def data(self) -> List[StockItem]:
        """Return list of all stock items."""
        return self.db.query(StockItem).all()

    def update(self, name: str, quantity_delta: float):
        """
        Change stock quantity by quantity_delta (positive for income, negative for expense).
        
        Args:
            name: Stock item name
            quantity_delta: Change amount (positive or negative)
            
        Raises:
            ValueError: If result would be negative
            KeyError: If item not found
        """
        # Get current item
        current_item = self.get(name)
        if current_item is None:
            raise KeyError(f"Stock item '{name}' not found")
        
        new_quantity = current_item.quantity + quantity_delta
        
        # Check business logic: disallow negative stock
        if new_quantity < 0:
            raise ValueError(
                f"Insufficient stock for '{name}'. Need to deduct {abs(quantity_delta):.2f}, "
                f"current stock {current_item.quantity:.2f}."
            )
        
        try:
            current_item.quantity = new_quantity
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Error updating stock for '{name}': {e}")
        
    def set(self, name: str, new_quantity: float):
        """
        Set new quantity value for stock item.
        
        Args:
            name: Stock item name
            new_quantity: New quantity value
            
        Raises:
            KeyError: If item not found
        """
        # Check item exists
        item = self.get(name)
        if item is None:
            raise KeyError(f"Stock item '{name}' not found")
        
        try:
            item.quantity = new_quantity
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Error updating stock for '{name}': {e}")

    def can_delete(self, name: str) -> bool:
        """Check if stock item can be deleted (not used in products)."""
        stock = self.get(name)
        if not stock:
            return True
        
        # Check if stock is used in product recipes
        from sql_model.entities import product_stock_association
        count = self.db.query(product_stock_association).filter(
            product_stock_association.c.stock_id == stock.id
        ).count()
        return count == 0

    def delete(self, name: str):
        """Delete stock item by name."""
        if not self.can_delete(name):
            raise ValueError(f"Material '{name}' is used in a product. Cannot delete.")
        
        stock = self.get(name)
        if not stock:
            return
        
        try:
            self._model.expense_types().delete(name)
            self.db.delete(stock)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
            
    def len(self) -> int:
        """Return count of stock items."""
        return self.db.query(StockItem).count()

    def empty(self) -> bool:
        """Check if stock is empty."""
        return self.len() == 0